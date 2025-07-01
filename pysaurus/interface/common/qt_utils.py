import logging
import sys
import threading
from abc import abstractmethod
from typing import Callable, Sequence, Type

from pysaurus.core.functions import identity

logger = logging.getLogger(__name__)
Types = Type | Sequence[Type]


class TypeValidator:
    __slots__ = "__types", "__wrapper", "__parser"

    def __init__(self, types: Types, wrapper: Callable = None, parser: Callable = None):
        self.__types = types
        self.__wrapper = wrapper
        self.__parser = parser or (
            self.__types if isinstance(self.__types, type) else identity
        )

    def __call__(self, value):
        assert isinstance(value, self.__types)
        return value if self.__wrapper is None else self.__wrapper(value)

    def parse(self, text: str):
        return self.__parser(text)


def parse_bool(value: str):
    return value.lower() not in ("false", "0")


TYPE_VALIDATORS = {
    str: TypeValidator(str),
    bool: TypeValidator(bool, parser=parse_bool),
    int: TypeValidator(int),
    float: TypeValidator((bool, int, float), float, float),
}


class Callback:
    def __init__(self, callback, *args):
        self.callback = callback
        self.args = args

    def __call__(self):
        return self.callback(*self.args)


class ExceptHookForQt:
    __slots__ = ("qt_app",)

    def __init__(self, qt_app):
        self.qt_app = qt_app

    def register(self):
        sys.excepthook = self.sys_except_hook
        threading.excepthook = self.thread_except_hook

    def sys_except_hook(self, cls, exception, trace):
        logger.error("[Qt] Error occurring.")
        sys.__excepthook__(cls, exception, trace)
        self.cleanup()
        self.qt_app.exit(1)

    def thread_except_hook(self, arg):
        logger.error(f"[Qt] Error occurring in thread: {arg.thread.name}")
        sys.__excepthook__(arg.exc_type, arg.exc_value, arg.exc_traceback)
        self.cleanup()
        self.qt_app.exit(1)

    @abstractmethod
    def cleanup(self):
        pass
