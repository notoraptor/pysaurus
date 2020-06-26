import enum
from abc import abstractmethod, ABC
from typing import List, Optional

unsigned_int = int
unsigned_float = float
not_null_unsigned_float = float


class GuiException(Exception):
    pass


class RootException(GuiException):
    pass


class LeafException(GuiException):
    pass


class Axis(enum.Enum):
    X = enum.auto()
    Y = enum.auto()


class Dimension(enum.Enum):
    WIDTH = enum.auto()
    HEIGHT = enum.auto()


class SizeComputer(ABC):
    @abstractmethod
    def compute(self, widget, dimension):
        # type: (Widget, Dimension) -> unsigned_int
        pass


class PositionComputer(ABC):
    @abstractmethod
    def compute(self, widget, axis):
        # type: (Widget, Axis) -> float
        pass


class DefaultSizeComputer(SizeComputer):
    def compute(self, widget, dimension):  # type: (Widget, Dimension) -> unsigned_int
        if dimension is Dimension.WIDTH:
            return widget.get_default_width()
        if dimension is Dimension.HEIGHT:
            return widget.get_default_height()


class DefaultPositionComputer(PositionComputer):
    def compute(self, widget, axis):  # type: (Widget, Axis) -> float
        if axis is Axis.X:
            return widget.get_default_x()
        if axis is Axis.Y:
            return widget.get_default_y()


DEFAULT_POSITION_COMPUTER = DefaultPositionComputer()
DEFAULT_SIZE_COMPUTER = DefaultSizeComputer()


class Node:
    # Static attributes.
    ALLOW_PARENT = True
    ALLOW_CHILDREN = True

    # Public methods.

    def __init__(self, parent=None):
        # type: (Node) -> None
        self.parent = None  # type: Optional[None]
        self.parent_index = -1
        self.children = []  # type: List[Node]
        if parent:
            parent.add_child(self)

    def __str__(self):
        return '%s%s' % (
            type(self).__name__,
            '(%s)' % ','.join(str(child) for child in self.children)
            if self.children else ''
        )

    def add_child(self, child):
        # type: (Node) -> None
        if not self.ALLOW_CHILDREN:
            raise LeafException(self)
        if not child.ALLOW_PARENT:
            raise RootException(child)
        if child.parent is self:
            return
        if child.parent:
            child.parent.remove_child(child)
        self.children.append(child)
        child.parent = self
        child.parent_index = len(self.children)

    def remove_child(self, child):
        if child.parent is self:
            self.children.pop(child.parent_index)
            child.parent = None
            child.parent_index = -1

    def set_children(self, children):
        removed_children = self.children
        self.children = []
        for removed_child in removed_children:
            removed_child.parent = None
            removed_child.parent_index = -1
        for child in children:
            self.add_child(child)

    def get_children(self):
        return list(self.children)

    def count_children(self):
        return len(self.children)

    def get_root(self):
        if self.parent:
            return self.parent.get_root()
        return self

    def is_root(self):
        return not self.ALLOW_PARENT

    def is_leaf(self):
        return not self.ALLOW_CHILDREN

    def is_like_root(self):
        return not self.parent

    def is_like_leaf(self):
        return not self.children


class Position:

    def __init__(self, widget, axis, *, computer=None, reference=None, value=None):
        self.widget = widget  # type: Widget
        self.axis = axis  # type: Axis
        self.computer = computer  # type: Optional[PositionComputer]
        self.reference = reference or self.widget.get_root()  # type: Optional[Widget]
        self.value = value  # type: int

    def compute(self):
        if self.computer:
            return self.computer.compute(self.widget, self.axis)
        if self.reference:
            return self.reference.get_axis(self.axis) + self.value
        return self.value

    @staticmethod
    def absolute(widget, axis, value):
        return Position(widget, axis, value=value)

    @staticmethod
    def relative(widget, axis, reference, value):
        return Position(widget, axis, reference=reference, value=value)

    @staticmethod
    def auto(widget, axis, computer):
        return Position(widget, axis, computer=computer)


class Size:

    def __init__(self, widget, dimension, *, computer=None, reference=None, a=None, b=None):
        self.widget = widget  # type: Widget
        self.dimension = dimension  # type: Dimension
        self.computer = computer  # type: Optional[SizeComputer]
        self.reference = reference  # type: Optional[Widget]
        self.a = a  # type: unsigned_float
        self.b = b  # type: unsigned_float

    def compute(self):
        if self.computer:
            return self.computer.compute(self.widget, self.dimension)
        if self.reference:
            return self.reference.get_dimension(self.dimension) * self.a / self.b
        return self.a / self.b

    @staticmethod
    def absolute(widget, dimension, value):
        return Size(widget, dimension, a=value, b=1)

    @staticmethod
    def relative(widget, dimension, reference, value):
        return Size(widget, dimension, reference=reference, a=value, b=1)

    @staticmethod
    def percent(widget, dimension, reference, value):
        return Size(widget, dimension, reference=reference, a=value, b=100)

    @staticmethod
    def auto(widget, dimension, computer):
        return Size(widget, dimension, computer=computer)


class Widget(Node):
    CONTEXTS = []

    x: Position
    y: Position
    width: Size
    height: Size

    def __init__(self, parent=None):
        if not parent and self.CONTEXTS:
            parent = self.CONTEXTS[-1]
        super().__init__(parent)
        self.x = Position.auto(self, Axis.X, DEFAULT_POSITION_COMPUTER)
        self.y = Position.auto(self, Axis.Y, DEFAULT_POSITION_COMPUTER)
        self.width = Size.auto(self, Dimension.WIDTH, DEFAULT_SIZE_COMPUTER)
        self.height = Size.auto(self, Dimension.HEIGHT, DEFAULT_SIZE_COMPUTER)

    def __enter__(self):
        self.CONTEXTS.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        last = self.CONTEXTS.pop()
        assert last is self

    def get_x(self):
        return self.x.compute()

    def get_y(self):
        return self.y.compute()

    def get_width(self):
        return self.width.compute()

    def get_height(self):
        return self.height.compute()

    def get_default_x(self):
        return 0

    def get_default_y(self):
        return 0

    def get_default_width(self):
        return 0

    def get_default_height(self):
        return 0

    def get_axis(self, axis: Axis):
        if axis == Axis.X:
            return self.get_x()
        if axis == Axis.Y:
            return self.get_y()

    def get_dimension(self, dimension: Dimension):
        if dimension == Dimension.WIDTH:
            return self.get_width()
        if dimension == Dimension.HEIGHT:
            return self.get_height()


class Window(Widget):
    ALLOW_PARENT = False


class Element(Widget):
    ALLOW_CHILDREN = False


def main():
    w = Window()
    with w:
        Element()
        Element()
        Element()
        Widget()
        Element()
        with Widget():
            Element()
            Widget()
            Element()
        Widget()
        Element()
        Element()
    print(w)


if __name__ == '__main__':
    main()
