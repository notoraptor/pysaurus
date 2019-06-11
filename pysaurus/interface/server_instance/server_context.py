import multiprocessing

from pysaurus.core.function_parsing.function_parser import FunctionParser
from pysaurus.interface.server_instance.core_notification_collector import CoreNotificationCollector


class ServerContext:
    __slots__ = ('api', 'multiprocessing_manager', 'collector', '__loading_status', 'function_parser')
    NOT_LOADED = 'DB_NOT_LOADED'
    LOADING = 'DB_LOADING'
    LOADED = 'DB_LOADED'

    def __init__(self):
        self.api = None
        self.function_parser = FunctionParser()
        self.multiprocessing_manager = multiprocessing.Manager()
        self.collector = CoreNotificationCollector(self.multiprocessing_manager.Queue())
        self.__loading_status = self.NOT_LOADED

    def not_loaded(self):
        return self.__loading_status == self.NOT_LOADED

    def is_loading(self):
        return self.__loading_status == self.LOADING

    def is_loaded(self):
        return self.__loading_status == self.LOADED

    def set_is_loading(self):
        self.__loading_status = self.LOADING

    def set_is_loaded(self):
        self.__loading_status = self.LOADED

    def get_loading_status(self):
        return self.__loading_status
