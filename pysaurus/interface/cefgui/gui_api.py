import multiprocessing
import queue
import threading
import time
import traceback
from abc import abstractmethod
from typing import Optional, Callable

from pysaurus.core.components import AbsolutePath, FilePath
from pysaurus.core.database.database_features import DatabaseFeatures
from pysaurus.core.database.viewport.video_provider import VideoProvider
from pysaurus.core.file_copier import FileCopier
from pysaurus.core.functions import launch_thread
from pysaurus.core.notifications import (
    Notification,
    End,
    Terminated,
    Cancelled,
    DatabaseReady,
)
from pysaurus.core.path_tree import PathTree
from pysaurus.interface.cefgui.feature_api import FeatureAPI
from pysaurus.interface.cefgui.parallel_notifier import ParallelNotifier


class GuiAPI(FeatureAPI):
    def __init__(self):
        self.multiprocessing_manager = multiprocessing.Manager()
        super().__init__(ParallelNotifier(self.multiprocessing_manager.Queue()))
        self.monitor_thread = None  # type: Optional[threading.Thread]
        self.db_loading_thread = None  # type: Optional[threading.Thread]
        self.threads_stop_flag = False
        self.copy_work: Optional[FileCopier] = None
        self.notifier.call_default_if_no_manager()

    def create_database(self, name, folders, update):
        def run():
            self._create_database(name, folders)
            if update:
                self._update_database()

        run.__name__ = "create_database"
        self._launch(run)

    def open_database(self, path, update):
        def run():
            self._open_database(path)
            if update:
                self._update_database()

        run.__name__ = "open_database"
        self._launch(run)

    def update_database(self):
        self._launch(self._update_database)

    def find_similar_videos(self):
        self._launch(self._find_similarities)

    def find_similar_videos_ignore_cache(self):
        self._launch(self._find_similarities_ignore_cache)

    def move_video_file(self, video_id, directory):
        def run():
            self._move_video_file(video_id, directory)

        run.__name__ = "move_video_file"
        self._launch(run, finish=False)

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
        self.threads_stop_flag = True
        if self.monitor_thread:
            self.monitor_thread.join()
        if self.db_loading_thread:
            self.db_loading_thread.join()
        print("App closed.")

    # Private methods.

    def _launch(self, function: Callable[[], None], finish=True):
        print("Running", function.__name__)
        assert not self.monitor_thread
        assert not self.db_loading_thread
        self.notifier.clear_managers()
        self._consume_notifications()

        if finish:

            def run():
                function()
                self._finish_loading(f"Finished running: {function.__name__}")

        else:
            run = function

        # Launch monitor thread.
        self.monitor_thread = launch_thread(self._monitor_notifications)
        # Then launch function.
        self.db_loading_thread = launch_thread(run)

    def _finish_loading(self, log_message):
        if self.provider:
            self.provider.register_notifications()
        self.notifier.notify(DatabaseReady())
        self.db_loading_thread = None
        print(log_message)

    def _consume_notifications(self):
        if self.notifier.queue.qsize():
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
            except Exception as exc:
                print("Exception while sending notification:")
                traceback.print_tb(exc.__traceback__)
                print(type(exc).__name__)
                print(exc)
        self.monitor_thread = None
        print("End monitoring.")

    @abstractmethod
    def _notify(self, notification):
        # type: (Notification) -> None
        raise NotImplementedError()

    def _create_database(self, name, folders):
        self.database = self.application.new_database(name, folders)
        self.provider = VideoProvider(self.database)

    def _open_database(self, path):
        self.database = self.application.open_database(path)
        self.provider = VideoProvider(self.database)

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
                raise ValueError(
                    "Directory is not in allowed video folders for this database."
                )
            dst = FilePath(
                directory, video.filename.file_title, video.filename.extension
            )
            self.copy_work = FileCopier(video.filename, dst, notifier=self.notifier)
            done = self.copy_work.move()
            self.copy_work = None
            if done:
                old_path = self.database.change_video_path(video, dst)
                if old_path:
                    old_path.delete()
                self.provider.refresh()
        except Exception as exc:
            self.database.notifier.notify(End(f"Error: {exc}"))
        finally:
            self.db_loading_thread = None
