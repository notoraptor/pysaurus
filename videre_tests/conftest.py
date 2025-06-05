import io

import pytest

from videre.windowing.windowfactory import WindowLD


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
