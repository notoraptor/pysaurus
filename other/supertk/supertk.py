import tkinter

from PIL import Image, ImageTk

TK_VERSION = tkinter.TkVersion
TCL_VERSION = tkinter.Tcl().eval("info patchlevel")
TCL_THREADED = tkinter.Tcl().eval("set tcl_platform(threaded)")
assert TCL_THREADED == "1"


def padding(left=0, top=None, right=None, bottom=None, /):
    if left is None:
        left = top = right = bottom = 0
    if top is None:
        top = right = bottom = left
    if right is None:
        right = left
        bottom = top
    if bottom is None:
        raise ValueError(
            f"Ambiguous padding ({left}, {top}, {right}). "
            f"Expected padding(all), padding(x, y) or padding(let, top, right, bottom)"
        )
    return left, top, right, bottom


class Sticky:
    TOP = tkinter.N
    LEFT = tkinter.W
    RIGHT = tkinter.E
    BOTTOM = tkinter.S

    FULL = (TOP, LEFT, RIGHT, BOTTOM)
    HORIZONTAL = (LEFT, RIGHT)
    VERTICAL = (TOP, BOTTOM)


class BorderRelief:
    FLAT = "flat"
    RAISED = "raised"
    SUNKEN = "sunken"
    SOLID = "solid"
    RIDGE = "ridge"
    GROOVE = "groove"


def open_image(path: str) -> ImageTk.PhotoImage:
    """
    Open an image and return it in an object to be used
    everywhere Tkinter's PhotoImage is accepted.
    :param path:
    :return:
    """
    image = Image.open(path)
    return ImageTk.PhotoImage(image)


class SystemName:
    WINDOWS = "win32"
    LINUX = "linux"
    MAC = "darwin"
