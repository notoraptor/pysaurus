import functools

from videre.windowing.step_window import StepWindow

WindowLD = functools.partial(StepWindow, width=320, height=240)
WindowSD = functools.partial(StepWindow, width=640, height=480)
WindowHD = functools.partial(StepWindow, width=1280, height=720)
WindowFHD = functools.partial(StepWindow, width=1920, height=1080)
