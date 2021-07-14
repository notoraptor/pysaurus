import multiprocessing
import queue
import threading
import time
import traceback
from abc import abstractmethod
from typing import Optional, Callable

from pysaurus.core.database.database import Database
from pysaurus.core.database.database_features import DatabaseFeatures
from pysaurus.core.database.viewport.video_provider import VideoProvider
from pysaurus.core.functions import launch_thread
from pysaurus.core.notifications import Notification, DatabaseReady
from pysaurus.core.testing import TEST_LIST_FILE_PATH
from pysaurus.interface.webtop.feature_api import FeatureAPI
from pysaurus.interface.webtop.parallel_notifier import ParallelNotifier


class GuiAPI(FeatureAPI):
    def __init__(self):
        self.multiprocessing_manager = multiprocessing.Manager()
        super().__init__(ParallelNotifier(self.multiprocessing_manager.Queue()))
        self.monitor_thread = None  # type: Optional[threading.Thread]
        self.db_loading_thread = None  # type: Optional[threading.Thread]
        self.threads_stop_flag = False
        self.__update_on_load = True
        self.__update_job = None
        self.notifier.call_default_if_no_manager()

    def _launch(self, function: Callable[[], None]):
        print("Running", function.__name__)
        assert not self.monitor_thread
        assert not self.db_loading_thread
        self.notifier.clear_managers()

        def run():
            function()
            self._finish_loading(f"Finished running: {function.__name__}")

        # Launch monitor thread.
        self.monitor_thread = launch_thread(self._monitor_notifications)
        # Then launch function.
        self.db_loading_thread = launch_thread(run)

    def _finish_loading(self, log_message):
        self.provider.register_notifications()
        self.notifier.notify(DatabaseReady())
        self.db_loading_thread = None
        print(log_message)

    def create_database(self, name, folders, update):
        self.__update_job = ("create", (name, folders))
        self.__update_on_load = update

    def open_database(self, path, update):
        self.__update_job = ("open", (path,))
        self.__update_on_load = update

    def close_database(self):
        self.database = None
        self.provider = None
        return self.list_databases()

    def load_database(self, update=True):
        self.__update_on_load = update
        self._launch(self._load_database)

    def update_database(self):
        self._launch(self._update_database)

    def find_similar_videos(self):
        self._launch(self._find_similarities)

    def find_similar_videos_ignore_cache(self):
        self._launch(self._find_similarities_ignore_cache)

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

    def _create_database(self, name, folders):
        self.database = self.application.new_database(name, folders)
        self.provider = VideoProvider(self.database)

    def _open_database(self, path):
        self.database = self.application.open_database(path)
        self.provider = VideoProvider(self.database)

    def _load_database(self):
        # Load database
        assert not self.database
        assert not self.provider
        update = self.__update_on_load
        self.__update_on_load = True
        self.database = Database.load_from_list_file_path(
            TEST_LIST_FILE_PATH,
            update=update,
            notifier=self.notifier,
            ensure_miniatures=True,
            reset=False,
        )
        self.provider = VideoProvider(self.database)

    def _update_database(self):
        update = self.__update_on_load
        job = self.__update_job
        self.__update_on_load = True
        self.__update_job = None
        if job:
            job_name, job_params = job
            if job_name == "create":
                print("RUN: Creating database")
                self._create_database(*job_params)
            else:
                assert job_name == "open"
                print("RUN: Opening database")
                self._open_database(*job_params)
        if update:
            print("RUN: Updating existing database")
            self.database.refresh(ensure_miniatures=True)
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
