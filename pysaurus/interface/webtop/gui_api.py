import multiprocessing
import queue
import threading
import time
import traceback
from abc import abstractmethod
from typing import Optional

from pysaurus.core.database.database import Database
from pysaurus.core.database.notifications import DatabaseReady
from pysaurus.core.database.viewport.video_provider import VideoProvider
from pysaurus.core.functions import launch_thread
from pysaurus.core.notification import Notification
from pysaurus.core.testing import TEST_LIST_FILE_PATH
from pysaurus.interface.webtop.feature_api import FeatureAPI
from pysaurus.interface.webtop.parallel_notifier import ParallelNotifier


class GuiAPI(FeatureAPI):
    def __init__(self):
        super().__init__()
        self.multiprocessing_manager = multiprocessing.Manager()
        self.notifier = ParallelNotifier(self.multiprocessing_manager.Queue())
        self.monitor_thread = None  # type: Optional[threading.Thread]
        self.db_loading_thread = None  # type: Optional[threading.Thread]
        self.threads_stop_flag = False
        self.__update_on_load = True
        self.notifier.call_default_if_no_manager()

    def load_database(self, update=True):
        assert not self.monitor_thread
        assert not self.db_loading_thread
        self.__update_on_load = update
        # Launch monitor thread.
        self.monitor_thread = launch_thread(self._monitor_notifications)
        # Then launch database loading thread.
        self.db_loading_thread = launch_thread(self._load_database)

    def update_database(self):
        assert not self.monitor_thread
        assert not self.db_loading_thread
        self.monitor_thread = launch_thread(self._monitor_notifications)
        self.db_loading_thread = launch_thread(self._update_database)

    def close_app(self):
        self.threads_stop_flag = True
        if self.monitor_thread:
            self.monitor_thread.join()
        if self.db_loading_thread:
            self.db_loading_thread.join()
        print("App closed.")

    # Private methods.

    def _monitor_notifications(self):
        print("Monitoring notifications ...")
        while True:
            if self.threads_stop_flag:
                break
            try:
                notification = self.notifier.queue.get_nowait()
                self._notify(notification)
                if isinstance(notification, DatabaseReady):
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

    def _load_database(self):
        self.notifier.clear_managers()
        update = self.__update_on_load
        self.__update_on_load = True
        self.database = Database.load_from_list_file_path(
            TEST_LIST_FILE_PATH,
            update=update,
            notifier=self.notifier,
            ensure_miniatures=True,
            reset=False,
        )
        self._load_videos()
        self.notifier.notify(DatabaseReady())
        self.db_loading_thread = None
        print("End loading database.")

    def _update_database(self):
        self.notifier.clear_managers()
        self.database.refresh(ensure_miniatures=True)
        self._load_videos()
        self.notifier.notify(DatabaseReady())
        self.db_loading_thread = None
        print("End updating database.")

    def _load_videos(self):
        if self.provider:
            self.provider.load()
        else:
            self.provider = VideoProvider(self.database)
        self.provider.register_notifications()
