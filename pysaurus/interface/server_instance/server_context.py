import multiprocessing

from pysaurus.interface.server_instance.core_notification_collector import CoreNotificationCollector


class ServerContext:
    __slots__ = ('interface', 'multiprocessing_manager', 'collector', 'loading_status')
    NOT_LOADED = 0
    LOADING = 1
    LOADED = 2

    def __init__(self):
        self.interface = None
        self.multiprocessing_manager = multiprocessing.Manager()
        self.collector = CoreNotificationCollector(self.multiprocessing_manager.Queue())
        self.loading_status = self.NOT_LOADED

    def not_loaded(self):
        return self.loading_status == self.NOT_LOADED

    def is_loading(self):
        return self.loading_status == self.LOADING

    def is_loaded(self):
        return self.loading_status == self.LOADED

    def set_is_loading(self):
        self.loading_status = self.LOADING

    def set_is_loaded(self):
        self.loading_status = self.LOADED
