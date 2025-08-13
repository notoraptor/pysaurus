import functools
import os

from videre_tests.testing.step_window import StepWindow

IMAGE_EXAMPLE = os.path.join(os.path.dirname(__file__), "flowers-7660120_640.jpg")
assert os.path.isfile(IMAGE_EXAMPLE)

LD = dict(width=320, height=240)
SD = dict(width=640, height=480)
HD = dict(width=1280, height=720)
FHD = dict(width=1920, height=1080)
WindowLD = functools.partial(StepWindow, **LD)
WindowSD = functools.partial(StepWindow, **SD)
WindowHD = functools.partial(StepWindow, **HD)
WindowFHD = functools.partial(StepWindow, **FHD)
