from abc import ABC, abstractmethod
from typing import Any, Iterable

from PIL.Image import Image


class AbstractImageProvider(ABC):
    __slots__ = ()

    @abstractmethod
    def count(self) -> int:
        pass

    @abstractmethod
    def items(self) -> Iterable[tuple[Any, Image]]:
        pass

    @abstractmethod
    def length(self, filename) -> float:
        pass

    @abstractmethod
    def similarity(self, filename) -> int | None:
        pass
