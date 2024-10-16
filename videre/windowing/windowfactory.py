import functools

from videre.windowing.window import Window

WindowLD = functools.partial(Window, width=320, height=240)
WindowSD = functools.partial(Window, width=640, height=480)
WindowHD = functools.partial(Window, width=1280, height=720)
WindowFHD = functools.partial(Window, width=1920, height=1080)
