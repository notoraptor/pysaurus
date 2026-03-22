"""
Tests for ProcessPage and its helper classes.

Tests the progress display page including JobProgressWidget,
ProcessNotificationCollector, and ProcessPage lifecycle.
"""

from pysaurus.core.job_notifications import JobToDo
from pysaurus.core.notifications import End


class TestJobProgressWidget:
    def test_creation(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import JobProgressWidget

        widget = JobProgressWidget("test_job", 100, "Test Job")
        qtbot.addWidget(widget)

        assert widget.name == "test_job"
        assert widget.total == 100
        assert widget.title == "Test Job"

    def test_title_label(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import JobProgressWidget

        widget = JobProgressWidget("job", 50, "My Title")
        qtbot.addWidget(widget)

        assert widget.title_label.text() == "My Title"

    def test_title_fallback_to_name(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import JobProgressWidget

        widget = JobProgressWidget("job_name", 50, "")
        qtbot.addWidget(widget)

        assert widget.title_label.text() == "job_name"

    def test_initial_progress(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import JobProgressWidget

        widget = JobProgressWidget("job", 100, "Test")
        qtbot.addWidget(widget)

        assert widget.progress_bar.value() == 0
        assert widget.percent_label.text() == "0%"

    def test_set_progress(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import JobProgressWidget

        widget = JobProgressWidget("job", 100, "Test")
        qtbot.addWidget(widget)

        widget.set_progress(50)
        assert widget.progress_bar.value() == 50
        assert widget.percent_label.text() == "50%"

    def test_set_progress_full(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import JobProgressWidget

        widget = JobProgressWidget("job", 200, "Test")
        qtbot.addWidget(widget)

        widget.set_progress(200)
        assert widget.progress_bar.value() == 200
        assert widget.percent_label.text() == "100%"

    def test_set_progress_zero_total(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import JobProgressWidget

        widget = JobProgressWidget("job", 0, "Test")
        qtbot.addWidget(widget)

        # Should not raise even with total=0
        widget.set_progress(0)
        assert widget.progress_bar.value() == 0


class TestProcessPage:
    def test_creation(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import ProcessPage

        page = ProcessPage("Updating database")
        qtbot.addWidget(page)

        assert "Updating database" in page.title_label.text()
        assert not page.btn_continue.isEnabled()

    def test_continue_button_disabled_initially(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import ProcessPage

        page = ProcessPage("Test")
        qtbot.addWidget(page)

        assert not page.btn_continue.isEnabled()

    def test_add_log_entry(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import ProcessPage

        page = ProcessPage("Test")
        qtbot.addWidget(page)

        initial_count = page.log_layout.count()
        page.add_log_entry("Hello log")

        assert page.log_layout.count() == initial_count + 1

    def test_add_empty_log_entry_ignored(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import ProcessPage

        page = ProcessPage("Test")
        qtbot.addWidget(page)

        initial_count = page.log_layout.count()
        page.add_log_entry("")

        assert page.log_layout.count() == initial_count

    def test_add_log_entry_bold(self, qtbot):
        from PySide6.QtWidgets import QLabel

        from pysaurus.interface.pyside6.pages.process_page import ProcessPage

        page = ProcessPage("Test")
        qtbot.addWidget(page)

        page.add_log_entry("Bold entry", bold=True)

        # Get the last label before the stretch
        label = page.log_layout.itemAt(page.log_layout.count() - 2).widget()
        assert isinstance(label, QLabel)
        assert "bold" in label.styleSheet().lower()

    def test_add_log_entry_color(self, qtbot):
        from PySide6.QtWidgets import QLabel

        from pysaurus.interface.pyside6.pages.process_page import ProcessPage

        page = ProcessPage("Test")
        qtbot.addWidget(page)

        page.add_log_entry("Red entry", color="red")

        label = page.log_layout.itemAt(page.log_layout.count() - 2).widget()
        assert isinstance(label, QLabel)
        assert "red" in label.styleSheet()

    def test_clear_log(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import ProcessPage

        page = ProcessPage("Test")
        qtbot.addWidget(page)

        page.add_log_entry("Entry 1")
        page.add_log_entry("Entry 2")
        page._clear_log()

        # Only the stretch item should remain
        assert page.log_layout.count() == 1

    def test_create_job_widget(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import ProcessPage

        page = ProcessPage("Test")
        qtbot.addWidget(page)

        job = JobToDo("extract_thumbs", 50, "Extracting thumbnails")
        widget = page.create_job_widget(job)

        assert widget.name == "extract_thumbs"
        assert widget.total == 50
        assert "extract_thumbs" in page._job_widgets

    def test_create_job_widget_replaces_existing(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import ProcessPage

        page = ProcessPage("Test")
        qtbot.addWidget(page)

        job1 = JobToDo("job", 10, "Job v1")
        page.create_job_widget(job1)

        job2 = JobToDo("job", 20, "Job v2")
        widget2 = page.create_job_widget(job2)

        assert page._job_widgets["job"] is widget2
        assert widget2.total == 20

    def test_on_end_notification(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import ProcessPage

        page = ProcessPage("Test")
        qtbot.addWidget(page)

        end = End("Done")
        page.on_notification(end)

        assert page.btn_continue.isEnabled()
        assert page._end_notification is end

    def test_on_continue_callback(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import ProcessPage

        results = []
        page = ProcessPage("Test", callback=lambda n: results.append(n))
        qtbot.addWidget(page)

        end = End("Done")
        page.on_notification(end)
        page._on_continue()

        assert len(results) == 1
        assert results[0] is end

    def test_on_continue_emits_signal(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import ProcessPage

        page = ProcessPage("Test")
        qtbot.addWidget(page)

        end = End("Done")
        page.on_notification(end)

        with qtbot.waitSignal(page.continue_clicked, timeout=1000):
            page._on_continue()

    def test_on_continue_without_end_notification(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import ProcessPage

        results = []
        page = ProcessPage("Test", callback=lambda n: results.append(n))
        qtbot.addWidget(page)

        # No end notification: callback should not be called
        page._on_continue()
        assert len(results) == 0

    def test_spinner_animating_initially(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import ProcessPage

        page = ProcessPage("Test")
        qtbot.addWidget(page)

        assert page.spinner._timer.isActive()
        assert not page.spinner._complete

    def test_spinner_complete_after_end(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import ProcessPage

        page = ProcessPage("Test")
        qtbot.addWidget(page)

        page.on_notification(End("Complete"))

        assert not page.spinner._timer.isActive()
        assert page.spinner._complete


class TestProcessNotificationCollector:
    def test_display_notification_adds_log(self, qtbot):
        from pysaurus.core.notifications import Message

        from pysaurus.interface.pyside6.pages.process_page import ProcessPage

        page = ProcessPage("Test")
        qtbot.addWidget(page)

        initial_count = page.log_layout.count()

        # Collect a simple notification
        page.collector._display_notification(Message("Hello"))

        assert page.log_layout.count() == initial_count + 1

    def test_new_progress_creates_widget(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import (
            ProcessJobProgress,
            ProcessPage,
        )

        page = ProcessPage("Test")
        qtbot.addWidget(page)

        job = JobToDo("my_job", 30, "My Job")
        progress = page.collector._new_progress(job)

        assert isinstance(progress, ProcessJobProgress)
        assert "my_job" in page._job_widgets


class TestProcessJobProgress:
    def test_display_updates_widget(self, qtbot):
        from pysaurus.interface.pyside6.pages.process_page import (
            JobProgressWidget,
            ProcessJobProgress,
        )

        job = JobToDo("job", 100, "Job")
        widget = JobProgressWidget("job", 100, "Job")
        qtbot.addWidget(widget)

        progress = ProcessJobProgress(job, widget)
        progress._display(42)

        assert widget.progress_bar.value() == 42
        assert widget.percent_label.text() == "42%"
