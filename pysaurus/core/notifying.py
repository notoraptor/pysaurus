from typing import Callable, Dict, Optional, TypeVar

from pysaurus.core.components import Date
from pysaurus.core.notifications import Notification

N = TypeVar("N", bound=Notification)
ManagerType = Callable[[N], None]


class Notifier:
    __slots__ = (
        "__managers",
        "__default_manager",
        "__default_manager_policy",
        "__log_path",
        "__log_written",
    )

    DM_NO_CALL = 0
    DM_CALL_IF_NO_MANAGER = 1
    DM_CALL_SOONER = 2
    DM_CALL_LATER = 3

    def manage(self, notification):
        print(notification)

    def __init__(self):
        self.__managers = {}  # type: Dict[type, ManagerType]
        self.__default_manager = None  # type: Optional[Callable[[Notification], None]]
        self.__default_manager_policy = Notifier.DM_CALL_SOONER
        self.__log_path = None
        self.__log_written = False

    def __call__(self, notification):
        return self.notify(notification)

    def set_log_path(self, path: Optional[str]):
        if self.__log_path != path:
            self.__log_written = False
        self.__log_path = path
        print(f"{type(self).__name__}: logging into: {self.__log_path}")

    def log(self, notification):
        if self.__log_path:
            with open(self.__log_path, "a", encoding="utf-8") as file:
                if not self.__log_written:
                    file.write(f"\n########## LOG {Date.now()} ##########\n\n")
                    self.__log_written = True
                line = f"{notification}\n"
                file.write(line)

    def set_default_manager(self, function):
        # type: (ManagerType) -> None
        self.__default_manager = function

    def never_call_default_manager(self):
        self.__default_manager_policy = Notifier.DM_NO_CALL

    def call_default_if_no_manager(self):
        self.__default_manager_policy = Notifier.DM_CALL_IF_NO_MANAGER

    def call_default_manager_sooner(self):
        self.__default_manager_policy = Notifier.DM_CALL_SOONER

    def call_default_manager_later(self):
        self.__default_manager_policy = Notifier.DM_CALL_LATER

    def set_manager(self, notification_class, function):
        # type: (type, ManagerType) -> None
        self.__managers[notification_class] = function

    def get_manager(self, notification):
        return self.__managers.get(type(notification), None)

    def remove_manager(self, notification_class):
        # type: (type) -> None
        self.__managers.pop(notification_class, None)

    def clear_managers(self):
        self.__managers.clear()

    def get_default_manager(self):
        return self.__default_manager or self.manage

    def notify(self, notification):
        # type: (Notification) -> None
        self.log(notification)
        default_manager = self.get_default_manager()
        notification_class = type(notification)
        if self.__default_manager_policy == Notifier.DM_CALL_SOONER:
            default_manager(notification)
        if notification_class in self.__managers:
            self.__managers[notification_class](notification)
        elif self.__default_manager_policy == Notifier.DM_CALL_IF_NO_MANAGER:
            default_manager(notification)
        if self.__default_manager_policy == Notifier.DM_CALL_LATER:
            default_manager(notification)


DEFAULT_NOTIFIER = Notifier()

GLOBAL_SETTING_LOG: bool = True
GLOBAL_SETTING_HANDLER: Optional[Callable[[Notification], None]] = None


def config(log=None, handler=None):
    global GLOBAL_SETTING_LOG
    global GLOBAL_SETTING_HANDLER
    if log is not None:
        GLOBAL_SETTING_LOG = bool(log)
    if handler is not None:
        assert callable(handler)
    GLOBAL_SETTING_HANDLER = handler


def notify(notification: Notification):
    if GLOBAL_SETTING_LOG and GLOBAL_SETTING_HANDLER is None:
        print(notification)
    if GLOBAL_SETTING_HANDLER is not None:
        GLOBAL_SETTING_HANDLER(notification)


def with_handler(handler, function, *args):
    config(handler=handler)
    ret = function(*args)
    config(handler=None)
    return ret
