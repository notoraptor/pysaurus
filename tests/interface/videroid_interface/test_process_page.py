"""Coverage for the transient ProcessPage (progress + notifications)."""

import videre

from pysaurus.core.job_notifications import JobProgressDisplay, JobToDo
from pysaurus.core.notifications import DatabaseReady, End, Message
from pysaurus.interface.videroid.pages.process_page import ProcessPage
from tests.interface.videroid_interface._widget_tree import find as _find
from tests.interface.videroid_interface._widget_tree import texts as _texts


class TestProcessPage:
    def test_build_shows_title(self):
        page = ProcessPage("Updating database", lambda end: None)
        widget = page.get_widget()
        assert isinstance(widget, videre.Column)
        assert "Updating database ..." in _texts(widget)  # title rendered

    def test_message_notification_is_displayed(self):
        page = ProcessPage("Scan", lambda end: None)
        page.on_notification(Message("working"))  # collect + _refresh_view, not End
        assert "working" in _texts(page._view)  # the message text really shows

    def test_end_shows_continue_and_calls_on_end(self):
        captured = []
        page = ProcessPage("X", captured.append)
        end = DatabaseReady()
        page.on_notification(end)  # End -> _finish (Continue button)
        footer = page._footer.controls
        assert len(footer) == 1 and isinstance(footer[0], videre.Button)
        page._on_continue(None)
        assert captured == [end]

    def test_display_job_progress_shows_percent_and_bar(self):
        page = ProcessPage("X", lambda end: None)
        view = JobProgressDisplay(JobToDo("scan", 4))  # no title -> falls back to name
        view.channels[None] = 2  # current = 2 / total 4 -> 50%
        widget = page._display(view)
        assert isinstance(widget, videre.Row)
        assert "scan (50 %)" in _texts(widget)  # computed percent label
        assert _find(widget, videre.ProgressBar)  # and a progress bar

    def test_display_end_message_and_fallback(self):
        page = ProcessPage("X", lambda end: None)
        end = End()
        assert page._display(end).text == str(end)  # End -> str(view)
        assert page._display(Message("m")).text == "m"  # Message -> its text
        sentinel = object()
        assert page._display(sentinel).text == str(sentinel)  # fallback str()
