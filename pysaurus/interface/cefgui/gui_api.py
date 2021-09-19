import multiprocessing
import queue
import threading
import time
from abc import abstractmethod
from typing import Optional, Callable, Sequence, Dict

from pysaurus.application import exceptions
from pysaurus.core.components import AbsolutePath
from pysaurus.core.file_copier import FileCopier
from pysaurus.core.functions import launch_thread
from pysaurus.core.notifications import (
    Notification,
    End,
    Done,
    Terminated,
    Cancelled,
    DatabaseReady,
)
from pysaurus.core.path_tree import PathTree
from pysaurus.database.viewport.video_provider import VideoProvider
from pysaurus.interface.cefgui import tk_utils
from pysaurus.interface.cefgui.feature_api import FeatureAPI
from pysaurus.interface.cefgui.parallel_notifier import ParallelNotifier

try:
    from pysaurus.database.database_features import DatabaseFeatures
    COMPARISON_ENABLED = True
except exceptions.CysaurusUnavailable:
    COMPARISON_ENABLED = False
    import sys
    print("Video thumbnails comparison unavailable.", file=sys.stderr)


class GuiAPI(FeatureAPI):
    def __init__(self, monitor_notifications=True):
        self.multiprocessing_manager = multiprocessing.Manager()
        super().__init__(ParallelNotifier(self.multiprocessing_manager.Queue()))
        self.monitor_thread = None  # type: Optional[threading.Thread]
        self.db_loading_thread = None  # type: Optional[threading.Thread]
        self.threads_stop_flag = False
        self.copy_work: Optional[FileCopier] = None
        self.notifier.call_default_if_no_manager()
        self.monitor_notifications = monitor_notifications

    def get_constants(self, **kwargs):
        return super().get_constants(PYTHON_FEATURE_COMPARISON=COMPARISON_ENABLED)

    def create_database(self, name, folders, update):
        self._launch(self._create_database, args=(name, folders, update))

    def open_database(self, path, update):
        self._launch(self._open_database, args=(path, update))

    def update_database(self):
        self._launch(self._update_database)

    def find_similar_videos(self):
        self._launch(self._find_similarities)

    def find_similar_videos_ignore_cache(self):
        self._launch(self._find_similarities_ignore_cache)

    def move_video_file(self, video_id, directory):
        self._launch(self._move_video_file, args=(video_id, directory), finish=False)

    def cancel_copy(self):
        if self.copy_work is not None:
            self.copy_work.cancel = True
        else:
            self.database.notifier.notify(Cancelled())

    def close_database(self):
        self.database = None
        self.provider = None
        return self.list_databases()

    def delete_database(self):
        assert self.application.delete_database(self.database.folder)
        self.database = None
        self.provider = None
        return self.list_databases()

    def close_app(self):
        # Close threads.
        self.threads_stop_flag = True
        if self.monitor_thread:
            self.monitor_thread.join()
        if self.db_loading_thread:
            self.db_loading_thread.join()
        # Close manager.
        self.notifier.queue = None
        self.notifier = None
        self.multiprocessing_manager = None
        # App closed.
        print("App closed.")

    # Private methods.

    def _launch(
        self,
        function: Callable,
        args: Sequence = None,
        kwargs: Dict = None,
        finish=True,
    ):
        print("Running", function.__name__)
        args = args or ()
        kwargs = kwargs or {}
        assert not self.monitor_thread
        assert not self.db_loading_thread
        self.notifier.clear_managers()
        self._consume_notifications()

        if finish:

            def run(*a, **k):
                function(*a, **k)
                self._finish_loading(f"Finished running: {function.__name__}")

        else:
            run = function

        # Launch monitor thread.
        if self.monitor_notifications:
            self.monitor_thread = launch_thread(self._monitor_notifications)
        # Then launch function.
        self.db_loading_thread = launch_thread(run, *args, **kwargs)

    def _finish_loading(self, log_message):
        if self.provider:
            self.provider.register_notifications()
        self.notifier.notify(DatabaseReady())
        self.db_loading_thread = None
        print(log_message)

    def _consume_notifications(self):
        while True:
            try:
                self.notifier.queue.get_nowait()
            except queue.Empty:
                break
        assert not self.notifier.queue.qsize()

    def _monitor_notifications(self):
        print("Monitoring notifications ...")
        while True:
            if self.threads_stop_flag:
                break
            try:
                notification = self.notifier.queue.get_nowait()
                self._notify(notification)
                if isinstance(notification, Terminated):
                    break
            except queue.Empty:
                time.sleep(1 / 100)
        self.monitor_thread = None
        print("End monitoring.")

    @abstractmethod
    def _notify(self, notification):
        # type: (Notification) -> None
        raise NotImplementedError()

    def _create_database(self, name: str, folders: Sequence[str], update: bool):
        self.database = self.application.new_database(name, folders)
        self.provider = VideoProvider(self.database)
        if update:
            self._update_database()

    def _open_database(self, path: str, update: bool):
        self.database = self.application.open_database(path)
        self.provider = VideoProvider(self.database)
        if update:
            self._update_database()

    def _update_database(self):
        self.database.refresh(ensure_miniatures=False)
        self.provider.refresh()

    def _find_similarities(self):
        DatabaseFeatures.find_similar_videos(self.database)
        self.provider.set_groups(
            field="similarity_id",
            is_property=False,
            sorting="field",
            reverse=False,
            allow_singletons=False,
        )
        self.provider.refresh()

    def _find_similarities_ignore_cache(self):
        DatabaseFeatures.find_similar_videos_ignore_cache(self.database)
        self.provider.set_groups(
            field="similarity_id",
            is_property=False,
            sorting="field",
            reverse=False,
            allow_singletons=False,
        )
        self.provider.refresh()

    def _move_video_file(self, video_id, directory):
        self.provider.register_notifications()
        try:
            video = self.database.get_video_from_id(video_id)
            directory = AbsolutePath.ensure_directory(directory)
            if not PathTree(self.database.video_folders).in_folders(directory):
                raise exceptions.ForbiddenVideoFolder(
                    directory, self.database.video_folders
                )
            dst = AbsolutePath.file_path(
                directory, video.filename.file_title, video.filename.extension
            )
            self.copy_work = FileCopier(
                video.filename, dst, notifier=self.notifier, notify_end=False
            )
            done = self.copy_work.move()
            self.copy_work = None
            if done:
                old_path = self.database.change_video_path(video, dst)
                if old_path:
                    old_path.delete()
                self.provider.refresh()
                self.notifier.notify(Done())
            else:
                self.notifier.notify(Cancelled())
        except Exception as exc:
            self.database.notifier.notify(End(f"Error {type(exc).__name__}: {exc}"))
        finally:
            self.db_loading_thread = None

    @staticmethod
    def clipboard(text):
        tk_utils.clipboard_set(text)

    def clipboard_video_path(self, video_id):
        tk_utils.clipboard_set(self.database.get_from_id(video_id).filename.path)

    @staticmethod
    def select_directory(default=None):
        return tk_utils.select_directory(default)

    @staticmethod
    def select_files():
        return tk_utils.select_many_files_to_open()

    @staticmethod
    def select_file():
        return tk_utils.select_file_to_open()
