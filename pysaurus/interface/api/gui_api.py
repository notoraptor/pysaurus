import functools
import logging
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
from pysaurus.core.job_notifications import ConsoleJobProgress, JobStep, JobToDo
from pysaurus.core.modules import System as OS
from pysaurus.core.notifications import (
    Cancelled,
    DatabaseReady,
    Done,
    End,
    Notification,
)
from pysaurus.core.notifying import Notifier
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler, ProfilingEnd, ProfilingStart
from pysaurus.database import pattern_detection
from pysaurus.database.db_features import DbFeatures
from pysaurus.database.db_video_server import ServerLauncher
from pysaurus.interface.api import tk_utils
from pysaurus.interface.api.feature_api import (
    FeatureAPI,
    ProxyFeature,
    YieldNotification,
)
from pysaurus.interface.api.parallel_notifier import ParallelNotifier
from saurus.language import say

logger = logging.getLogger(__name__)

process = Runnable("_launch")

if OS.is_windows():
    VLC_PATH = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
else:
    VLC_PATH = "vlc"


class FromTk(ProxyFeature):
    def __init__(self, method, returns=False):
        super().__init__(getter=lambda: tk_utils, method=method, returns=returns)


class ProviderNotifier(Notifier):
    __slots__ = ()

    def __init__(self):
        super().__init__()
        # self.call_default_if_no_manager()

    def manage(self, notification):
        # has_manager = self.get_manager(notification) is not None
        # logger.warning(f"[provider-notifier:{has_manager}] {notification}")
        pass


class ConsoleNotificationPrinter:
    __slots__ = ("_prev_profiling_start", "progress")

    def __init__(self):
        self._prev_profiling_start: ProfilingStart = None
        self.progress: ConsoleJobProgress = None

    def print(self, notification):
        prev_profiling_start = self._prev_profiling_start
        self._prev_profiling_start = None
        if isinstance(notification, ProfilingStart):
            if prev_profiling_start:
                print("!", prev_profiling_start)
            self._prev_profiling_start = notification
        elif isinstance(notification, ProfilingEnd):
            if prev_profiling_start:
                assert prev_profiling_start.name == notification.name
                print(f"Profiled({notification.name}, {notification.time})")
            else:
                print(notification)
        else:
            if prev_profiling_start:
                print("?", prev_profiling_start)

            if isinstance(notification, JobToDo):
                progress = self.progress
                assert not progress or progress.done
                self.progress = ConsoleJobProgress(notification)
            elif isinstance(notification, JobStep):
                self.progress.update(notification)
            else:
                print(notification)


class GuiAPI(FeatureAPI):
    __slots__ = (
        "multiprocessing_manager",
        "notification_thread",
        "launched_thread",
        "threads_stop_flag",
        "copy_work",
        "monitor_notifications",
        "server",
        "_provider_notifier",
    )

    def __init__(self, monitor_notifications=True):
        # Here to receive provider notification managers
        # instead of self.notifier, because self.notifier is used in multiprocessing,
        # and we don't want to pickle provider in sub-processes
        # (heavy, remember provider contains database, and some data can't be pickled)
        self._provider_notifier = ProviderNotifier()
        self.multiprocessing_manager = multiprocessing.Manager()
        super().__init__(
            notifier=ParallelNotifier(self.multiprocessing_manager),
            local_notifier=self._provider_notifier,
        )
        self.notification_thread: Optional[threading.Thread] = None
        self.launched_thread: Optional[threading.Thread] = None
        self.threads_stop_flag = False
        self.copy_work: Optional[FileCopier] = None
        self.notifier.call_default_if_no_manager()
        self.monitor_notifications = monitor_notifications
        self.server = ServerLauncher(lambda: self.database)

        self.server.start()
        # TODO Check runtime VLC for other OS ?
        self._constants.update(
            {
                "PYTHON_HAS_RUNTIME_VLC": OS.is_windows() and os.path.isfile(VLC_PATH),
                "PYTHON_SERVER_HOSTNAME": self.server.server_thread.hostname,
                "PYTHON_SERVER_PORT": self.server.server_thread.port,
            }
        )
        self._proxies.update(
            {
                "clipboard": FromTk(tk_utils.clipboard_set),
                "select_directory": FromTk(tk_utils.select_directory, True),
                "select_file": FromTk(tk_utils.select_file_to_open, True),
            }
        )

    def __run_feature__(self, name: str, *args) -> Optional:
        # Launch notification thread on first API call from frontend.
        # This let time for frontend to be loaded before receiving notifications.
        if self.monitor_notifications and self.notification_thread is None:
            logger.debug("Starting notification thread")
            self.notification_thread = self._run_thread(self._monitor_notifications)
        return super().__run_feature__(name, *args)

    def open_from_server(self, video_id) -> str:
        hostname = self.server.server_thread.hostname
        port = self.server.server_thread.port
        url = f"http://{hostname}:{port}/video/{video_id}"
        logger.debug(f"Running {VLC_PATH} {url}")
        self._run_thread(subprocess.run, [VLC_PATH, url])
        return url

    def create_prediction_property(self, prop_name) -> None:
        self.database.create_prop_type(f"<?{prop_name}>", int, [-1, 0, 1], False)

    def cancel_copy(self) -> None:
        if self.copy_work is not None and not self.copy_work.terminated:
            self.copy_work.cancel = True
        else:
            self.database.notifier.notify(Cancelled())

    def close_database(self) -> None:
        self._provider_notifier.clear_managers()
        self.database = None

    def delete_database(self) -> None:
        self._provider_notifier.clear_managers()
        assert self.application.delete_database_from_name(self.database.name)
        self.database = None

    def close_app(self) -> None:
        logger.debug("Closing app ...")
        # Close threads.
        self.threads_stop_flag = True
        if self.notification_thread:
            self.notification_thread.join()
        if self.launched_thread:
            self.launched_thread.join()
        # Close manager.
        self.notifier.close()
        self.notifier = None
        self.multiprocessing_manager = None
        # Close server.
        self.server.stop()
        # App closed.
        logger.debug("App closed.")

    def _run_thread(self, function, *args, **kwargs) -> threading.Thread:
        return launch_thread(function, *args, **kwargs)

    def _launch(
        self,
        function: Callable,
        args: Sequence = None,
        kwargs: Dict = None,
        finish=True,
    ) -> None:
        logger.debug(f"Running {function.__name__}")
        args = args or ()
        kwargs = kwargs or {}
        assert self.notification_thread
        assert not self.launched_thread
        self._consume_notifications()

        if finish:

            @functools.wraps(function)
            def run(*a, **k):
                function(*a, **k)
                self._finish_loading(f"Finished running: {function.__name__}")

        else:
            run = function

        # Then launch function.
        self.launched_thread = self._run_thread(run, *args, **kwargs)

    def _finish_loading(self, log_message) -> None:
        self.notifier.notify(DatabaseReady())
        self.launched_thread = None
        logger.debug(log_message)

    def _get_latest_notifications(self) -> YieldNotification:
        return self.__consume_shared_queue(self.notifier.local_queue)

    def _consume_notifications(self) -> None:
        list(self.__consume_shared_queue(self.notifier.queue))

    @classmethod
    def __consume_shared_queue(cls, shared_queue) -> YieldNotification:
        while True:
            try:
                yield shared_queue.get_nowait()
            except queue.Empty:
                break
        assert not shared_queue.qsize()

    def _monitor_notifications(self) -> None:
        logger.debug("Monitoring notifications ...")
        # We are in a thread, with notifications handled sequentially,
        # thus no need to be process-safe.
        notification_printer = ConsoleNotificationPrinter()
        while True:
            if self.threads_stop_flag:
                break
            try:
                notification = self.notifier.queue.get_nowait()
                # self._provider_notifier.notify(notification)
                notification_printer.print(notification)
                self._notify(notification)
            except queue.Empty:
                time.sleep(1 / 100)
        self.notification_thread = None
        logger.debug("End monitoring.")

    @abstractmethod
    def _notify(self, notification: Notification) -> None:
        raise NotImplementedError()

    @process()
    def create_database(self, name: str, folders: Sequence[str], update: bool) -> None:
        with Profiler("Create database", self.application.notifier):
            self.database = self.application.new_database(name, folders)
            if update:
                self._update_database()
            self.database.provider.register_notifications(self._provider_notifier)

    @process()
    def open_database(self, name: str, update: bool) -> None:
        with Profiler("Open database", self.application.notifier):
            self.database = self.application.open_database_from_name(name)
            if update:
                self._update_database()
            self.database.provider.register_notifications(self._provider_notifier)

    @process()
    def update_database(self) -> None:
        self._update_database()

    def _update_database(self) -> None:
        self.database.refresh()
        self.database.provider.refresh()

    @process()
    def find_similar_videos(self) -> None:
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
    def find_similar_videos_ignore_cache(self) -> None:
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
    def move_video_file(self, video_id: int, directory: str) -> None:
        try:
            filename: AbsolutePath = self.database.read_video_field(
                video_id, "filename"
            )
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
            logger.exception("Error when moving")
            self.notifier.notify(
                End(
                    say("Error {name}: {message}", name=type(exc).__name__, message=exc)
                )
            )
        finally:
            self.launched_thread = None

    @process()
    def compute_predictor(self, prop_name) -> None:
        pattern_detection.compute_pattern_detector(
            self.database,
            self.database.get_cached_videos("readable", "with_thumbnails"),
            prop_name,
        )

    @process()
    def apply_predictor(self, prop_name) -> None:
        output_prop_name = pattern_detection.predict_pattern(
            self.database,
            self.database.get_cached_videos("readable", "with_thumbnails"),
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
