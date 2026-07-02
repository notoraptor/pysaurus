"""Coverage for the transient ProcessPage (progress + notifications)."""

import videre

from pysaurus.core.job_notifications import JobProgressDisplay, JobToDo
from pysaurus.core.notifications import DatabaseReady, End, Message
from pysaurus.database.algorithms.folder_scan import FolderScanProgress
from pysaurus.interface.videroid.pages.process_page import ProcessPage
from tests.interface.videroid_interface._widget_tree import find as _find
from tests.interface.videroid_interface._widget_tree import texts as _texts


class TestProcessPage:
    def test_build_shows_title(self):
        page = ProcessPage("Updating database", lambda end: None)
        widget = page.get_widget()
        assert isinstance(widget, videre.Column)
        assert "Updating database ..." in _texts(widget)  # title rendered

    def test_message_goes_to_log_not_jobs(self):
        page = ProcessPage("Scan", lambda end: None)
        page.on_notification(Message("working"))  # collect + refresh, not End
        assert "working" in _texts(page._log)  # the message shows in the log zone
        assert "working" not in _texts(page._jobs)  # ...and NOT in the jobs zone

    def test_continue_disabled_until_end_then_calls_on_end(self):
        captured = []
        page = ProcessPage("X", captured.append)
        assert page._continue.disabled is True  # disabled while running
        end = DatabaseReady()
        page.on_notification(end)  # End -> _finish enables Continue
        assert page._continue.disabled is False
        page._on_continue(None)  # click Continue
        assert captured == [end]

    def test_autocontinue_skips_the_button(self):
        captured = []
        page = ProcessPage("X", captured.append, autocontinue=True)
        end = DatabaseReady()
        page.on_notification(end)  # autocontinue -> on_end fired immediately
        assert captured == [end]

    def test_job_progress_goes_to_jobs_zone_with_percent_and_bar(self):
        page = ProcessPage("X", lambda end: None)
        view = JobProgressDisplay(JobToDo("scan", 4))  # no title -> name fallback
        view.channels[None] = 2  # current = 2 / total 4 -> 50%
        row = page._job_row(view)
        assert isinstance(row, videre.Row)
        assert "scan (50 %)" in _texts(row)  # computed percent label
        assert _find(row, videre.ProgressBar)  # and a progress bar

    def test_log_row_end_message_and_fallback(self):
        page = ProcessPage("X", lambda end: None)
        end = End()
        assert page._log_row(end).text == str(end)  # End -> str(view)
        assert page._log_row(Message("m")).text == "m"  # Message -> its text
        sentinel = object()
        assert page._log_row(sentinel).text == str(sentinel)  # fallback str()

    def test_scan_progress_feeds_dedicated_bar_not_the_log(self):
        page = ProcessPage("Scan", lambda end: None)
        # Hidden until the first scan notification (holder shows an EmptyWidget).
        assert page._scan_holder.control is not page._scan_row
        page.on_notification(FolderScanProgress(3, 12, 120))
        assert page._scan_holder.control is page._scan_row  # bar revealed
        assert page._scan_bar.value == 3 / 12
        assert page._scan_label.text == "3 / 12 folders — 120 files"
        # Kept OUT of the log/collector (would flood at ~5 Hz).
        assert page._collector.views == []
        assert "folders" not in " ".join(_texts(page._log))
        # The max grows as subfolders are discovered during the walk.
        page.on_notification(FolderScanProgress(10, 40, 500))
        assert page._scan_bar.value == 10 / 40

    def test_scan_progress_zero_discovered_no_crash(self):
        page = ProcessPage("Scan", lambda end: None)
        page.on_notification(FolderScanProgress(0, 0, 0))  # max(1, 0) guard
        assert page._scan_bar.value == 0.0
        assert page._scan_label.text == "0 / 0 folders — 0 files"

    def test_clear_log_hides_prior_entries_but_keeps_new_ones(self):
        page = ProcessPage("X", lambda end: None)
        page.on_notification(Message("first"))
        page.on_notification(Message("second"))
        assert "first" in _texts(page._log) and "second" in _texts(page._log)
        page._clear_log(None)  # hide the two entries
        assert "first" not in _texts(page._log)
        assert "second" not in _texts(page._log)
        page.on_notification(Message("third"))  # new entries still appear
        assert "third" in _texts(page._log)
