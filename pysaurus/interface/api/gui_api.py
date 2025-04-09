import functools
import logging
import os
import subprocess
import threading
from abc import abstractmethod
from typing import Callable, Dict, Optional, Sequence

import pyperclip

from pysaurus.application import exceptions
from pysaurus.core import tk_utils
from pysaurus.core.classes import Runnable
from pysaurus.core.components import AbsolutePath
from pysaurus.core.file_copier import FileCopier
from pysaurus.core.functions import launch_thread
from pysaurus.core.informer import INFORMER_CALLBACK, Informer
from pysaurus.core.modules import System
from pysaurus.core.notifications import (
    Cancelled,
    DatabaseReady,
    Done,
    End,
    Notification,
)
from pysaurus.core.path_tree import PathTree
from pysaurus.core.profiling import Profiler
from pysaurus.database.db_video_server import ServerLauncher
from pysaurus.database.features.db_similar_videos import DbSimilarVideos
from pysaurus.interface.api.api_utils.proxy_feature import FromPyperclip, FromTk
from pysaurus.interface.api.api_utils.vlc_path import VLC_PATH
from pysaurus.interface.api.feature_api import FeatureAPI
from saurus.language import say

logger = logging.getLogger(__name__)

process = Runnable("_launch")


class GuiAPI(FeatureAPI):
    __slots__ = ("launched_thread", "copy_work", "server", "_closed")

    def __init__(self):
        """
        *** Reminder ***
        When using multiprocessing, make sure to not share anything,
        especially objects linked to database, because
        database may contain data that can't be pickled.
        E.g. Do not share database provider.
        """
        informer = Informer.default()
        super().__init__(notifier=informer)
        self.launched_thread: Optional[threading.Thread] = None
        self.copy_work: Optional[FileCopier] = None
        self.server = ServerLauncher(lambda: self.database)
        self._closed = False

        INFORMER_CALLBACK.set_manager(self._notification_callback)

        self.server.start()
        # TODO Check runtime VLC for other operating systems ?
        self._constants.update(
            {
                "PYTHON_HAS_RUNTIME_VLC": (
                    System.is_windows() and os.path.isfile(VLC_PATH)
                ),
                "PYTHON_SERVER_HOSTNAME": self.server.server_thread.hostname,
                "PYTHON_SERVER_PORT": self.server.server_thread.port,
            }
        )
        self._proxies.update(
            {
                "clipboard": FromPyperclip(pyperclip.copy),
                "select_directory": FromTk(tk_utils.select_directory, True),
                "select_file": FromTk(tk_utils.select_file_to_open, True),
            }
        )

    def open_from_server(self, video_id) -> str:
        hostname = self.server.server_thread.hostname
        port = self.server.server_thread.port
        url = f"http://{hostname}:{port}/video/{video_id}"
        logger.debug(f"Running {VLC_PATH} {url}")
        self._run_thread(subprocess.run, [VLC_PATH, url])
        return url

    def cancel_copy(self) -> None:
        if self.copy_work is not None and not self.copy_work.terminated:
            self.copy_work.cancel = True
        else:
            self.database.notifier.notify(Cancelled())

    def close_database(self) -> None:
        self.database = None

    def delete_database(self) -> None:
        assert self.application.delete_database_from_name(self.database.get_name())
        self.database = None

    def close_app(self) -> None:
        logger.debug("Closing app ...")
        # Close threads.
        if self.launched_thread:
            self.launched_thread.join()
            self.launched_thread = None
        # Close manager.
        self.notifier = None
        # Close server.
        self.server.stop()
        # App closed.
        logger.debug("App closed.")

    def __close__(self):
        """Close GUI API."""
        if self._closed:
            print("[gui api] already closed.")
            return
        self.application.__close__()
        self._closed = True
        print("[gui api] closed.")

    def _run_thread(self, function, *args, **kwargs) -> threading.Thread:
        return launch_thread(function, *args, **kwargs)

    def _launch(
        self, fn: Callable, args: Sequence = None, kwargs: Dict = None, finish=True
    ) -> None:
        logger.debug(f"Running {fn.__name__}")
        args = args or ()
        kwargs = kwargs or {}
        assert self.launched_thread is None

        if finish:

            @functools.wraps(fn)
            def run(*a, **k):
                try:
                    fn(*a, **k)
                finally:
                    self._finish_loading(f"Finished running: {fn.__name__}")

        else:
            run = fn

        # Then launch function.
        self.launched_thread = self._run_thread(run, *args, **kwargs)

    def _finish_loading(self, log_message) -> None:
        self.notifier.notify(DatabaseReady())
        self.launched_thread = None
        logger.debug(log_message)

    def _notification_callback(self, notification: Notification):
        if self.database:
            Informer.log(str(self.database.ways.db_log_path), notification)
        self._notify(notification)

    @abstractmethod
    def _notify(self, notification: Notification) -> None:
        raise NotImplementedError()

    @process()
    def create_database(self, name: str, folders: Sequence[str], update: bool) -> None:
        self.database = self.application.new_database(name, folders, update)

    @process()
    def open_database(self, name: str, update: bool) -> None:
        self.database = self.application.open_database_from_name(name, update)

    @process()
    def update_database(self) -> None:
        self.database.refresh()

    @process()
    def find_similar_videos(self) -> None:
        DbSimilarVideos.find_similar_videos(self.database)
        self.database.provider.set_groups(
            field="similarity_id",
            is_property=False,
            sorting="field",
            reverse=False,
            allow_singletons=False,
        )

    @process(finish=False)
    def move_video_file(self, video_id: int, directory: str) -> None:
        try:
            filename: AbsolutePath = self.database.get_video_filename(video_id)
            directory = AbsolutePath.ensure_directory(directory)
            if not PathTree(self.database.get_folders()).in_folders(directory):
                raise exceptions.ForbiddenVideoFolder(
                    directory, list(self.database.get_folders())
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
                old_path = self.database.change_video_entry_filename(video_id, dst)
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
