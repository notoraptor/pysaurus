from typing import Callable, Dict

from pysaurus.core.classes import ToDict


class Notification(ToDict):
    __slots__ = []


ManagerType = Callable[[Notification], None]


class Notifier:
    __slots__ = ('__managers', '__default_manager', '__default_manager_policy')

    DM_NO_CALL = 0
    DM_CALL_BEFORE = 1
    DM_CALL_AFTER = 2

    @staticmethod
    def __default_manager_function(notification):
        print(notification)

    def __init__(self):
        self.__managers = {}  # type: Dict[type, ManagerType]
        self.__default_manager = None
        self.__default_manager_policy = Notifier.DM_CALL_BEFORE

    def set_default_manager(self, function):
        # type: (ManagerType) -> None
        self.__default_manager = function

    def never_call_default_manager(self):
        self.__default_manager_policy = Notifier.DM_NO_CALL

    def call_default_manager_before(self):
        self.__default_manager_policy = Notifier.DM_CALL_BEFORE

    def call_default_manager_after(self):
        self.__default_manager_policy = Notifier.DM_CALL_AFTER

    def set_manager(self, notification_class, function):
        # type: (type, ManagerType) -> None
        self.__managers[notification_class] = function

    def remove_manager(self, notification_class):
        # type: (type) -> None
        self.__managers.pop(notification_class, None)

    def clear_managers(self):
        self.__managers.clear()

    def get_default_manager(self):
        return self.__default_manager or Notifier.__default_manager_function

    def notify(self, notification):
        # type: (Notification) -> None
        default_manager = self.get_default_manager()
        if self.__default_manager_policy == Notifier.DM_CALL_BEFORE:
            default_manager(notification)
        notification_class = type(notification)
        if notification_class in self.__managers:
            self.__managers[notification_class](notification)
        if self.__default_manager_policy == Notifier.DM_CALL_AFTER:
            default_manager(notification)


DEFAULT_NOTIFIER = Notifier()
