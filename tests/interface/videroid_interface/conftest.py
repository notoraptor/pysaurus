"""Pytest fixtures for the videroid (videre) interface tests.

videroid is driven headless with videre's `StepWindow` / `FakeUser` (no Qt).
The backend (`GuiAPI`) is wired SYNCHRONOUSLY: we patch the Flask server
(`ServerLauncher`) and the home-dir-scanning `Application` (exactly like
`kyuti_interface/test_app_context.py`), build the real `VideroidContext`, then
inject an in-memory SQL database. So we exercise the REAL videroid code, not a
mock context.

`FakeWindow`/`fake_win`/`snap_win` mirror videre's own test conftest so videroid
widget tests can snapshot — these are candidates to factor into `videre.testing`
later.
"""

import io
from contextlib import contextmanager
from typing import Callable, Iterator
from unittest.mock import patch

import pytest
from videre.testing.step_window import StepWindow
from videre.testing.utils import LD

from pysaurus.interface.videroid.app import VideroidApp
from pysaurus.interface.videroid.context import VideroidContext

# --- backend wiring (no server, no real home scan) --------------------------

_SERVER = "pysaurus.interface.api.gui_api.ServerLauncher"
_APPLICATION = "pysaurus.interface.api.feature_api.Application"


@contextmanager
def _headless_backend(db_names: list[str] | None = None):
    """Patch out the Flask server + home-dir Application while a GuiAPI is built.

    `db_names` configures `application.get_database_names()` (used by the
    Databases page); leave None when a test only needs an injected database.
    """
    with patch(_SERVER), patch(_APPLICATION) as mock_app:
        mock_app.return_value.get_database_names.return_value = db_names or []
        yield


def make_context(database=None) -> VideroidContext:
    """A real VideroidContext with `database` injected (no server/home scan)."""
    with _headless_backend():
        ctx = VideroidContext()
    ctx._api.database = database
    return ctx


@pytest.fixture
def videroid_context(mem_saurus_database) -> VideroidContext:
    """Real VideroidContext backed by the small in-memory `test_database`."""
    return make_context(mem_saurus_database)


@pytest.fixture
def videroid_context_example(example_saurus_database_memory) -> VideroidContext:
    """Real VideroidContext backed by `example_db_in_pysaurus` (90 videos)."""
    return make_context(example_saurus_database_memory)


@pytest.fixture
def videroid_app(mem_saurus_database) -> Iterator[tuple[VideroidApp, StepWindow]]:
    """A real VideroidApp on a headless StepWindow, db injected, on Videos page."""
    with _headless_backend(), StepWindow() as window:
        app = VideroidApp(window=window)
        app.context._api.database = mem_saurus_database
        app.show_page("videos")
        window.render()
        yield app, window


# --- rendering / snapshot helpers (mirrors videre's tests/conftest.py) -------

ImageCheck = Callable[..., None]


class FakeWindow(StepWindow):
    __slots__ = ("_image_check", "_node_name")

    def __init__(self, image_check: ImageCheck, node_name: str, **kwargs):
        super().__init__(**kwargs)
        self._image_check = image_check
        self._node_name = node_name

    def check(self, basename: str | None = None):
        kwargs = {}
        if basename:
            kwargs["basename"] = f"{self._node_name}_{basename}"
        self.render()
        self._image_check(self.screenshot(), **kwargs)


@pytest.fixture
def _image_testing(image_regression):
    errors: list[AssertionError] = []

    def check(image: io.BytesIO, **kwargs):
        try:
            image_regression.check(image.getvalue(), diff_threshold=0, **kwargs)
        except AssertionError as e:
            errors.append(e)

    yield check

    if errors:
        raise AssertionError(
            f"{len(errors)} snapshot(s) diverged in this test:\n"
            + "\n".join(str(e) for e in errors)
        )


@pytest.fixture
def fake_win(_image_testing, request) -> Iterator[FakeWindow]:
    with FakeWindow(
        image_check=_image_testing, node_name=request.node.name, **LD
    ) as window:
        yield window


@pytest.fixture
def snap_win(fake_win) -> Iterator[FakeWindow]:
    yield fake_win
    fake_win.check()
