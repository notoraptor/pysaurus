import io

import pytest

from videre.windowing.step_window import StepWindow
from videre.windowing.windowfactory import WindowLD
from videre_tests.common import FakeUser


@pytest.fixture
def image_testing(image_regression):
    def check(image: io.BytesIO, **kwargs):
        image_regression.check(image.getvalue(), diff_threshold=0, **kwargs)

    return check


@pytest.fixture
def window_testing():
    with WindowLD() as window:
        yield window


@pytest.fixture
def snapwin(image_testing):
    with WindowLD() as window:
        yield window
        image_testing(window.snapshot())


@pytest.fixture
def fake_user():
    yield FakeUser


@pytest.fixture
def fake_win(image_testing, request):
    class FakeWindow(StepWindow):

        def __init__(self):
            super().__init__(width=320, height=240)

        def check(self, basename: str | None = None):
            kwargs = {}
            if basename:
                kwargs["basename"] = f"{request.node.name}_{basename}"
            image_testing(self.snapshot(), **kwargs)

    with FakeWindow() as window:
        yield window
