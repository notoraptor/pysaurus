from enum import Enum, auto
from typing import Any, List


###########################
# Graphical User Interface.
###########################

# Utilities.
# ----------

class Side(Enum):
    TOP = auto()
    RIGHT = auto()
    BOTTOM = auto()
    LEFT = auto()


class Padding:
    top: int
    right: int
    bottom: int
    left: int


# Menus
# -----


class MenuItem:
    title: str


class Action(MenuItem):
    action: callable


class Menu(MenuItem):
    children: List[MenuItem]


class ContextMenu(Menu):
    pass


# Abstract widgets
# ----------------


class Widget:
    allow_context_menu: bool = False
    context_menu: ContextMenu


class ActiveWidget(Widget):
    disabled: bool = False


class StateWidget(ActiveWidget):
    on_change: callable


class Container(Widget):
    children: List[Widget]


# Abstract widgets with rendering
# -------------------------------


class AbstractButton(ActiveWidget):
    title: str


class Scrollable(Widget):
    horizontal: bool = True
    vertical: bool = True
    widget: Widget


# Layouts
# -------


class Column(Container):
    pass


class Row(Container):
    pass


class BorderLayout(Container):
    top_left: Side = Side.TOP
    top_right: Side = Side.TOP
    bottom_left: Side = Side.BOTTOM
    bottom_right: Side = Side.BOTTOM


# Widgets
# -------

class Label(ActiveWidget):
    """ One-line text unit with one associated text style. """
    # Dimensions are exclusively defined by text style.
    # SOLID
    title: str
    on_click: callable


class RadioButton(ActiveWidget):
    # SOLID
    selected: bool


class Checkbox(StateWidget):
    # SOLID
    checked: bool


class Image(Widget):
    # Default dimensions are image dimensions.
    # Absolute dimensions can be specified.
    src: str
    width: int = -1
    height: int = -1


class TextInput(StateWidget):
    """ Editable one-line text unit with one associated text style. """
    # Text dimensions are defined by text style.
    width: int
    height: int
    padding: Padding


class SelectOption(Widget):
    # DEPENDENT: Select
    title: str
    value: Any


class Select(StateWidget):
    default: int = 0


class Button(AbstractButton):
    on_click: callable


class SubmitButton(AbstractButton):
    # Should have a form as ancestor.
    pass


class ProgressBar(ActiveWidget):
    value: float
    total: float


# Conceptual widgets.
# -------------------


class RadioButtonGroup(StateWidget, Container):
    # NO SIZE
    pass


class Form(Container):
    # NO SIZE
    on_submit: callable
    on_change: callable


# Frames and dialogs.
# -------------------


class Frame(Container):
    title: str


class Dialog(Frame):
    pass


class Confirm(Dialog):
    action: callable


# High-level widgets.
# -------------------


class FolderInput:
    pass


class Spoiler:
    pass


class TabGroup:
    pass


# Specific widgets for Pysaurus web interface.
# --------------------------------------------


class VideoFolders:
    pass


class NotificationInterface:
    pass
