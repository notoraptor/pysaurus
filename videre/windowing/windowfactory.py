import functools

from videre.windowing.step_window import StepWindow

LD = dict(width=320, height=240)
SD = dict(width=640, height=480)
HD = dict(width=1280, height=720)
FHD = dict(width=1920, height=1080)

WindowLD = functools.partial(StepWindow, **LD)
WindowSD = functools.partial(StepWindow, **SD)
WindowHD = functools.partial(StepWindow, **HD)
WindowFHD = functools.partial(StepWindow, **FHD)
