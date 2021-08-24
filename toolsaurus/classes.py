from abc import abstractmethod
from typing import Generic, List

from pysaurus.core.classes import T


class Context:
    __slots__ = ["_context"]

    def __init__(self):
        self._context = False

    def __getattribute__(self, item):
        if not object.__getattribute__(self, "_context"):
            raise RuntimeError(f"{type(self).__name__} object not used as a context")
        return object.__getattribute__(self, item)

    @abstractmethod
    def on_exit(self):
        pass

    def __enter__(self):
        self._context = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ret = self.on_exit()
        self._context = False
        return ret


class ListView(Generic[T]):
    __slots__ = ("__seq", "__start", "__end")

    def __init__(self, sequence, start, end):
        # type: (List[T], int, int) -> None
        self.__seq = sequence
        self.__start = max(len(sequence) + start if start < 0 else start, 0)
        self.__end = min(
            max(len(sequence) + end if end < 0 else end, self.__start), len(sequence)
        )

    def __len__(self):
        return self.__end - self.__start

    def __bool__(self):
        return self.__end != self.__start

    def __getitem__(self, item):
        return self.__seq[self.__end + item if item < 0 else self.__start + item]

    def __iter__(self):
        return (self.__seq[i] for i in range(self.__start, self.__end))
