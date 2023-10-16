from abc import ABC, abstractmethod
from typing import Any, Iterable, Tuple

from PIL.Image import Image


class AbstractImageProvider(ABC):
    __slots__ = ()

    @abstractmethod
    def count(self) -> int:
        pass

    @abstractmethod
    def items(self) -> Iterable[Tuple[Any, Image]]:
        pass
