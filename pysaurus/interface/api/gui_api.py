import multiprocessing
import os
import queue
import subprocess
import threading
import time
from abc import abstractmethod
from typing import Callable, Dict, Optional, Sequence

from pysaurus.application import exceptions
from pysaurus.core.classes import Runnable
from pysaurus.core.components import AbsolutePath
from pysaurus.core.file_copier import FileCopier
from pysaurus.core.functions import launch_thread
from pysaurus.core.modules import System
from pysaurus.core.notifications import (
    Cancelled,
    DatabaseReady,
    Done,
    End,
    Notification,
    Terminated,
)
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler
from pysaurus.database import pattern_detection
from pysaurus.database.db_features import DbFeatures
from pysaurus.database.db_video_server import ServerLauncher
from pysaurus.interface.api import tk_utils
from pysaurus.interface.api.feature_api import FeatureAPI, ProxyFeature
from pysaurus.interface.api.parallel_notifier import ParallelNotifier
from saurus.language import say

process = Runnable("_launch")

if System.is_windows():
    VLC_PATH = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
else:
    VLC_PATH = "vlc"


class FromTk(ProxyFeature):
    def __init__(self, method, returns=False):
        super().__init__(getter=lambda: tk_utils, method=method, returns=returns)


class GuiAPI(FeatureAPI):
    __slots__ = (
        "multiprocessing_manager",
        "monitor_thread",
        "db_loading_thread",
        "threads_stop_flag",
        "copy_work",
        "monitor_notifications",
        "server",
    )

    def __init__(self, monitor_notifications=True):
        self.multiprocessing_manager = multiprocessing.Manager()
        super().__init__(ParallelNotifier(self.multiprocessing_manager.Queue()))
        self.monitor_thread: Optional[threading.Thread] = None
        self.db_loading_thread: Optional[threading.Thread] = None
        self.threads_stop_flag = False
        self.copy_work: Optional[FileCopier] = None
        self.notifier.call_default_if_no_manager()
        self.monitor_notifications = monitor_notifications
        self.server = ServerLauncher(lambda: self.database)
        self.server.start()
        self._proxies.update(
            {
                "clipboard": FromTk(tk_utils.clipboard_set),
                "select_directory": FromTk(tk_utils.select_directory, True),
                "select_files": FromTk(tk_utils.select_many_files_to_open, True),
                "select_file": FromTk(tk_utils.select_file_to_open, True),
            }
        )

    @property
    def PYTHON_HAS_RUNTIME_VLC(self):
        if System.is_windows():
            vlc_win_path = VLC_PATH
            return os.path.isfile(vlc_win_path)
        else:
            # TODO
            return False

    @property
    def PYTHON_SERVER_HOSTNAME(self):
        return self.server.server_thread.hostname

    @property
    def PYTHON_SERVER_PORT(self):
        return self.server.server_thread.port

    # Public tasks

    def open_from_server(self, video_id):
        url = f"http://{self.PYTHON_SERVER_HOSTNAME}:{self.PYTHON_SERVER_PORT}/video/{video_id}"
        print("Running", VLC_PATH, url)

        def play():
            subprocess.run([VLC_PATH, url])

        self._run_thread(play)
        return url

    def open_video_surely(self, video_id: int):
        try:
            self.database.open_video(video_id)
            return None
        except OSError:
            return self.open_from_server(video_id)

    def create_prediction_property(self, prop_name):
        self.database.create_prop_type(f"<?{prop_name}>", int, [-1, 0, 1], False)

    def cancel_copy(self):
        if self.copy_work is not None:
            self.copy_work.cancel = True
        else:
            self.database.notifier.notify(Cancelled())

    def close_database(self):
        self.database = None

    def delete_database(self):
        assert self.application.delete_database_from_name(self.database.name)
        self.database = None

    def close_app(self):
        print("Closing app ...")
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
        # Close server.
        self.server.stop()
        # App closed.
        print("App closed.")

    # Private methods.

    def _run_thread(self, function, *args, **kwargs):
        return launch_thread(function, *args, **kwargs)

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
            self.monitor_thread = self._run_thread(self._monitor_notifications)
        # Then launch function.
        self.db_loading_thread = self._run_thread(run, *args, **kwargs)

    def _finish_loading(self, log_message):
        if self.database:
            self.database.provider.register_notifications()
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

    @process()
    def create_database(self, name: str, folders: Sequence[str], update: bool):
        with Profiler("Create database", self.application.notifier):
            self.database = self.application.new_database(name, folders)
            if update:
                self._update_database()

    @process()
    def open_database(self, name: str, update: bool):
        with Profiler("Open database", self.application.notifier):
            self.database = self.application.open_database_from_name(name)
            if update:
                self._update_database()

    @process()
    def update_database(self):
        self._update_database()

    def _update_database(self):
        self.database.refresh()
        self.database.provider.refresh()

    @process()
    def find_similar_videos(self):
        DbFeatures().find_similar_videos(self.database)
        self.database.provider.set_groups(
            field="similarity_id",
            is_property=False,
            sorting="field",
            reverse=False,
            allow_singletons=False,
        )
        self.database.provider.refresh()

    @process()
    def find_similar_videos_ignore_cache(self):
        DbFeatures().find_similar_videos_ignore_cache(self.database)
        self.database.provider.set_groups(
            field="similarity_id",
            is_property=False,
            sorting="field",
            reverse=False,
            allow_singletons=False,
        )
        self.database.provider.refresh()

    @process(finish=False)
    def move_video_file(self, video_id: int, directory: str):
        self.database.provider.register_notifications()
        try:
            filename = self.database.get_video_filename(video_id)
            directory = AbsolutePath.ensure_directory(directory)
            if not PathTree(self.database.video_folders).in_folders(directory):
                raise exceptions.ForbiddenVideoFolder(
                    directory, self.database.video_folders
                )
            dst = AbsolutePath.file_path(
                directory, filename.file_title, filename.extension
            )
            self.copy_work = FileCopier(
                filename, dst, notifier=self.notifier, notify_end=False
            )
            with Profiler(say("Move"), notifier=self.notifier):
                done = self.copy_work.move()
            self.copy_work = None
            if done:
                old_path = self.database.change_video_path(video_id, dst)
                if old_path:
                    old_path.delete()
                self.database.provider.refresh()
                self.notifier.notify(Done())
            else:
                self.notifier.notify(Cancelled())
        except Exception as exc:
            self.database.notifier.notify(
                End(
                    say("Error {name}: {message}", name=type(exc).__name__, message=exc)
                )
            )
        finally:
            self.db_loading_thread = None

    @process()
    def compute_predictor(self, prop_name):
        pattern_detection.compute_pattern_detector(
            self.database,
            self.database.get_videos("readable", "with_thumbnails"),
            prop_name,
        )

    @process()
    def apply_predictor(self, prop_name):
        output_prop_name = pattern_detection.predict_pattern(
            self.database,
            self.database.get_videos("readable", "with_thumbnails"),
            prop_name,
        )
        self.database.provider.set_groups(
            field=output_prop_name,
            is_property=True,
            sorting="field",
            reverse=False,
            allow_singletons=True,
        )
        self.database.provider.refresh()
