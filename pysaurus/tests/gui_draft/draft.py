from pysaurus.core.classes import Fraction

class Node:
    has_parent = True
    has_children = False

    def get_parent(self):
        pass

    def set_parent(self, parent):
        pass

    def children(self):
        pass

    def count_children(self):
        pass

    def get_child(self, index):
        pass

    def set_child(self, index, child):
        pass

    def set_children(self, children):
        pass

    def append_child(self, child):
        pass

    def append_children(self, children):
        pass

    def clear_children(self):
        pass

    def remove_child(self, child_or_index):
        pass


class unsigned_int(int):
    def __init__(self, value):
        super().__init__(value)
        assert self >= 0


class Position:
    reference = None  # type: Widget  # default reference: parent
    value = 0


class AutoPosition:
    computer = None


class Size:
    value: unsigned_int = 0


class RelativeSize:
    reference = None  # type: Widget
    value = 0
    # percent
    # fraction


class AutoSize:
    computer = None


class Widget(Node):
    def get_width(self):
        pass

    def get_height(self):
        pass

    def get_x(self):
        pass

    def get_y(self):
        pass
