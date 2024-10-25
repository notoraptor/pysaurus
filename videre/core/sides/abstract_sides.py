from typing import Optional

from videre.core.constants import Side


class AbstractSides[T, S]:
    __slots__ = ("top", "right", "bottom", "left")
    __default__ = None

    def __init__(
        self,
        top: Optional[T] = None,
        left: Optional[T] = None,
        bottom: Optional[T] = None,
        right: Optional[T] = None,
    ):
        self.top = self._parse(top)
        self.left = self._parse(left)
        self.bottom = self._parse(bottom)
        self.right = self._parse(right)

    def _parse(self, value: Optional[T]):
        return self.__default__ if value is None else self.__parser__(value)

    def __parser__(self, value: T) -> S:
        return value

    def __repr__(self):
        sides = []
        for side in Side:
            value = getattr(self, side.value)
            if value is not None:
                sides.append(f"{side.value}={value}")
        return f"{type(self).__name__}({', '.join(sides)})"

    def __hash__(self):
        return hash((self.top, self.right, self.bottom, self.left))

    def __eq__(self, other):
        return type(self) is type(other) and (
            self.top == other.top
            and self.right == other.right
            and self.bottom == self.bottom
            and self.left == other.left
        )

    @classmethod
    def axis(cls, horizontal: Optional[T] = None, vertical: Optional[T] = None):
        return cls(top=horizontal, bottom=horizontal, left=vertical, right=vertical)

    @classmethod
    def sides(cls, value: T, *axes: Side):
        return cls(**{axis.value: value for axis in set(axes)})
