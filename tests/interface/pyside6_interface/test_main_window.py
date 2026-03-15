"""
Tests for MainWindow.

Tests page navigation, menu state, session logging,
process page management, and state change handling.
"""

import pytest
from PySide6.QtCore import QEvent, QObject, Signal
from PySide6.QtWidgets import QMessageBox

from pysaurus.core.duration import Duration
from pysaurus.core.file_size import FileSize
from pysaurus.interface.pyside6.main_window import MainWindow
from pysaurus.video.video_search_context import VideoSearchContext


def _empty_video_search_context():
    """Return a minimal VideoSearchContext for mocking."""
    return VideoSearchContext(
        sources=None,
        grouping=None,
        classifier=None,
        group_id=0,
        search=None,
        sorting=None,
        selector=None,
        page_size=20,
        page_number=0,
        with_moves=False,
        result=[],
        nb_pages=1,
        view_count=0,
        selection_count=0,
        selection_duration=Duration(0),
        selection_file_size=FileSize(0),
        classifier_stats=[],
        source_count=0,
    )


class QMockAppContext(QObject):
    """Mock AppContext with Qt signals for MainWindow tests."""

    _notification_from_thread = Signal(object)
    _exception_from_thread = Signal(object)
    notification_received = Signal(object)
    database_ready = Signal()
    profiling_started = Signal(str)
    profiling_ended = Signal(str, str)
    operation_done = Signal()
    operation_cancelled = Signal()
    operation_ended = Signal(str)
    job_started = Signal(str, int, str)
    job_progress = Signal(str, str, int, int, str)
    state_changed = Signal()

    def __init__(self):
        super().__init__()
        self._has_database = False
        self._database_name = ""
        self._database_folder = ""
        self._database_folders: list[str] = []
        self._database_names = ["test_db", "other_db"]
        self._notification_handler = None

    def has_database(self) -> bool:
        return self._has_database

    def get_database_name(self) -> str:
        return self._database_name

    def get_database_folder_path(self) -> str:
        return self._database_folder

    def get_database_folders(self) -> list[str]:
        return self._database_folders

    def get_database_names(self) -> list[str]:
        return self._database_names

    def get_prop_types(self, **kwargs) -> list:
        return []

    def get_videos(self, page_size, page_number, selector=None):
        if not self._has_database:
            return None
        return _empty_video_search_context()

    def close_database(self) -> None:
        self._has_database = False
        self._database_name = ""

    def close_app(self) -> None:
        pass

    def rename_database(self, new_name: str) -> None:
        self._database_name = new_name

    def set_database_folders(self, folders) -> None:
        self._database_folders = list(folders)

    def set_notification_handler(self, handler):
        self._notification_handler = handler

    def clear_notification_handler(self):
        self._notification_handler = None

    def delete_database_by_name(self, name: str) -> None:
        if name in self._database_names:
            self._database_names.remove(name)

    def open_database(self, name, update=True) -> None:
        self._has_database = True
        self._database_name = name

    def update_database(self) -> None:
        pass

    def find_similar_videos(self) -> None:
        pass

    def find_similar_videos_reencoded(self) -> None:
        pass

    def playlist(self) -> str:
        return ""

    # Simulate opening a database for tests
    def _simulate_open(self, name="test_db"):
        self._has_database = True
        self._database_name = name
        self._database_folder = f"/databases/{name}"
        self._database_folders = ["/videos"]


@pytest.fixture
def main_window(qtbot, monkeypatch):
    """Create a MainWindow with mocked AppContext."""
    from pysaurus.interface.pyside6 import main_window as mw_module

    monkeypatch.setattr(mw_module, "AppContext", QMockAppContext)

    from pysaurus.interface.pyside6.main_window import MainWindow

    window = MainWindow()
    # Disable closeEvent to prevent QMessageBox blocking during teardown
    window.closeEvent = lambda event: event.accept()
    qtbot.addWidget(window)
    return window


# =============================================================================
# Page navigation
# =============================================================================


class TestPageNavigation:
    """Tests for page navigation methods."""

    def test_initial_page_is_databases(self, main_window):
        assert main_window.stack.currentIndex() == MainWindow.PAGE_DATABASES

    def test_show_databases_page(self, main_window):
        main_window.show_databases_page()
        assert main_window.stack.currentIndex() == MainWindow.PAGE_DATABASES
        assert "Databases" in main_window.windowTitle()

    def test_show_videos_page_without_database_goes_to_databases(self, main_window):
        main_window.show_videos_page()
        # No database open => falls back to databases page
        assert main_window.stack.currentIndex() == MainWindow.PAGE_DATABASES

    def test_show_videos_page_with_database(self, main_window):
        main_window.ctx._simulate_open("my_db")
        main_window.show_videos_page()
        assert main_window.stack.currentIndex() == MainWindow.PAGE_VIDEOS
        assert "my_db" in main_window.windowTitle()

    def test_show_properties_page_without_database_goes_to_databases(self, main_window):
        main_window.show_properties_page()
        assert main_window.stack.currentIndex() == MainWindow.PAGE_DATABASES

    def test_show_properties_page_with_database(self, main_window):
        main_window.ctx._simulate_open("my_db")
        main_window.show_properties_page()
        assert main_window.stack.currentIndex() == MainWindow.PAGE_PROPERTIES
        assert "Properties" in main_window.windowTitle()
        assert "my_db" in main_window.windowTitle()

    def test_page_radio_switches_to_videos(self, main_window):
        main_window.ctx._simulate_open()
        main_window._on_page_radio_clicked(MainWindow.PAGE_VIDEOS)
        assert main_window.stack.currentIndex() == MainWindow.PAGE_VIDEOS

    def test_page_radio_switches_to_properties(self, main_window):
        main_window.ctx._simulate_open()
        main_window._on_page_radio_clicked(MainWindow.PAGE_PROPERTIES)
        assert main_window.stack.currentIndex() == MainWindow.PAGE_PROPERTIES


# =============================================================================
# Menu state
# =============================================================================


class TestMenuState:
    """Tests for menu enable/disable based on application state."""

    def test_database_actions_disabled_without_database(self, main_window):
        main_window._update_menu_state()
        assert main_window.database_menu.isEnabled()
        assert not main_window._action_rename_db.isEnabled()
        assert not main_window._action_close_db.isEnabled()
        assert not main_window._action_session_log.isEnabled()

    def test_database_actions_enabled_with_database(self, main_window):
        main_window.ctx._simulate_open()
        main_window._update_menu_state()
        assert main_window._action_rename_db.isEnabled()
        assert main_window._action_close_db.isEnabled()
        assert main_window._action_session_log.isEnabled()

    def test_view_menu_disabled_without_database(self, main_window):
        main_window._update_menu_state()
        assert not main_window.view_menu.isEnabled()

    def test_view_menu_enabled_on_videos_page(self, main_window):
        main_window.ctx._simulate_open()
        main_window.show_videos_page()
        assert main_window.view_menu.isEnabled()

    def test_view_menu_disabled_on_properties_page(self, main_window):
        main_window.ctx._simulate_open()
        main_window.show_properties_page()
        assert not main_window.view_menu.isEnabled()

    def test_selection_menu_disabled_without_database(self, main_window):
        main_window._update_menu_state()
        assert not main_window.selection_menu.isEnabled()

    def test_selection_menu_enabled_on_videos_page(self, main_window):
        main_window.ctx._simulate_open()
        main_window.show_videos_page()
        assert main_window.selection_menu.isEnabled()

    def test_page_selector_hidden_without_database(self, main_window):
        main_window._update_menu_state()
        assert not main_window._page_selector.isVisible()

    def test_page_selector_visible_with_database(self, main_window):
        main_window.ctx._simulate_open()
        main_window.show_videos_page()
        # isVisible() depends on parent visibility (window not shown in offscreen),
        # so check the explicit visibility flag instead.
        assert not main_window._page_selector.isHidden()

    def test_radio_synced_on_videos_page(self, main_window):
        main_window.ctx._simulate_open()
        main_window.show_videos_page()
        assert main_window._radio_videos.isChecked()

    def test_radio_synced_on_properties_page(self, main_window):
        main_window.ctx._simulate_open()
        main_window.show_properties_page()
        assert main_window._radio_properties.isChecked()


# =============================================================================
# Session logging
# =============================================================================


class TestSessionLogging:
    """Tests for session logging."""

    def test_session_log_starts_with_header(self, main_window):
        assert len(main_window._session_log) >= 3
        assert "Session started" in main_window._session_log[1]

    def test_log_message_appends_entry(self, main_window):
        count_before = len(main_window._session_log)
        main_window._log_message("test message")
        assert len(main_window._session_log) == count_before + 1
        assert "test message" in main_window._session_log[-1]

    def test_log_message_has_timestamp(self, main_window):
        main_window._log_message("timestamped")
        entry = main_window._session_log[-1]
        # Format: [YYYY-MM-DD HH:MM:SS] message
        assert entry.startswith("[")
        assert "]" in entry

    def test_session_log_dialog_creation(self, qtbot, main_window):
        from pysaurus.interface.pyside6.main_window import SessionLogDialog

        dialog = SessionLogDialog(main_window._session_log, main_window)
        qtbot.addWidget(dialog)
        assert "Session Log" in dialog.windowTitle()
        assert dialog.text_edit.toPlainText() != ""


# =============================================================================
# State change handling
# =============================================================================


class TestStateChangeHandling:
    """Tests for _on_state_changed refreshing the active page."""

    def test_state_changed_on_databases_page(self, main_window):
        """State change on databases page should not crash."""
        main_window.show_databases_page()
        main_window._on_state_changed()
        assert main_window.stack.currentIndex() == MainWindow.PAGE_DATABASES

    def test_state_changed_on_videos_page(self, main_window):
        """State change on videos page should refresh it."""
        main_window.ctx._simulate_open()
        main_window.show_videos_page()
        main_window._on_state_changed()
        assert main_window.stack.currentIndex() == MainWindow.PAGE_VIDEOS

    def test_state_changed_on_properties_page(self, main_window):
        """State change on properties page should refresh it."""
        main_window.ctx._simulate_open()
        main_window.show_properties_page()
        main_window._on_state_changed()
        assert main_window.stack.currentIndex() == MainWindow.PAGE_PROPERTIES


# =============================================================================
# Process page management
# =============================================================================


class TestProcessPage:
    """Tests for process page lifecycle."""

    def test_run_process_creates_process_page(self, main_window):
        main_window._run_process(
            title="Test Operation", operation=lambda: None, on_end=lambda end: None
        )
        assert main_window._process_page is not None
        assert "Test Operation" in main_window.windowTitle()

    def test_run_process_guard_prevents_concurrent(self, main_window):
        main_window._run_process(
            title="First", operation=lambda: None, on_end=lambda end: None
        )
        first_page = main_window._process_page

        main_window._run_process(
            title="Second", operation=lambda: None, on_end=lambda end: None
        )
        # Guard should prevent second process
        assert main_window._process_page is first_page

    def test_cleanup_process_page(self, main_window):
        main_window._run_process(
            title="Test", operation=lambda: None, on_end=lambda end: None
        )
        assert main_window._process_page is not None

        main_window._cleanup_process_page()
        assert main_window._process_page is None

    def test_cleanup_when_no_process_page(self, main_window):
        """Cleanup when no process page should not crash."""
        main_window._cleanup_process_page()
        assert main_window._process_page is None


# =============================================================================
# Status bar
# =============================================================================


class TestStatusBar:
    """Tests for status bar behavior."""

    def test_initial_status_message(self, main_window):
        assert main_window.status_bar.currentMessage() == "Ready"

    def test_status_message_from_page(self, main_window):
        main_window._on_status_message("Videos loaded: 42")
        assert "Videos loaded: 42" in main_window.status_bar.currentMessage()

    def test_status_message_logged(self, main_window):
        count_before = len(main_window._session_log)
        main_window._on_status_message("logged message")
        assert len(main_window._session_log) == count_before + 1

    def test_click_on_status_bar_clears_message(self, main_window):
        main_window.status_bar.showMessage("temporary")
        # Simulate mouse click via eventFilter
        event = QEvent(QEvent.Type.MouseButtonPress)
        result = main_window.eventFilter(main_window.status_bar, event)
        assert result is True
        assert main_window.status_bar.currentMessage() == ""

    def test_event_filter_ignores_other_objects(self, main_window):
        event = QEvent(QEvent.Type.MouseButtonPress)
        result = main_window.eventFilter(QObject(), event)
        assert result is False


# =============================================================================
# Options menu actions
# =============================================================================


class TestOptionsMenu:
    """Tests for options menu actions."""

    def test_confirm_not_found_setting(self, main_window):
        assert main_window.videos_page.confirm_not_found_deletion is True
        main_window._on_confirm_not_found_changed(False)
        assert main_window.videos_page.confirm_not_found_deletion is False
        main_window._on_confirm_not_found_changed(True)
        assert main_window.videos_page.confirm_not_found_deletion is True

    def test_toggle_show_only_selected(self, main_window):
        main_window._on_toggle_show_only_selected(True)
        assert main_window.videos_page.btn_show_only_selected.isChecked()
        main_window._on_toggle_show_only_selected(False)
        assert not main_window.videos_page.btn_show_only_selected.isChecked()


# =============================================================================
# Database menu actions
# =============================================================================


class TestDatabaseMenuActions:
    """Tests for database menu actions."""

    def test_rename_database_no_database(self, main_window):
        """Rename with no database should do nothing."""
        main_window._on_rename_database()
        # Should not crash

    def test_rename_database_success(self, main_window, monkeypatch):
        main_window.ctx._simulate_open("old_name")

        monkeypatch.setattr(
            "pysaurus.interface.pyside6.main_window.RenameDialog.get_name",
            lambda **kwargs: "new_name",
        )

        main_window._on_rename_database()
        assert main_window.ctx.get_database_name() == "new_name"
        assert "new_name" in main_window.windowTitle()

    def test_rename_database_cancelled(self, main_window, monkeypatch):
        main_window.ctx._simulate_open("old_name")

        monkeypatch.setattr(
            "pysaurus.interface.pyside6.main_window.RenameDialog.get_name",
            lambda **kwargs: None,
        )

        main_window._on_rename_database()
        assert main_window.ctx.get_database_name() == "old_name"

    def test_close_database_confirmed(self, main_window, monkeypatch):
        main_window.ctx._simulate_open("my_db")

        monkeypatch.setattr(
            QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.Yes
        )

        main_window._on_close_database()
        assert not main_window.ctx.has_database()
        assert main_window.stack.currentIndex() == MainWindow.PAGE_DATABASES

    def test_close_database_cancelled(self, main_window, monkeypatch):
        main_window.ctx._simulate_open("my_db")

        monkeypatch.setattr(
            QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.No
        )

        main_window._on_close_database()
        assert main_window.ctx.has_database()

    def test_edit_folders_no_database(self, main_window):
        """Edit folders with no database should do nothing."""
        main_window._on_edit_folders()


# =============================================================================
# Close event
# =============================================================================


class TestCloseEvent:
    """Tests for window close event (uses real closeEvent, not the fixture stub)."""

    def test_close_rejected(self, main_window, monkeypatch):
        monkeypatch.setattr(
            QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.No
        )

        from PySide6.QtGui import QCloseEvent

        event = QCloseEvent()
        MainWindow.closeEvent(main_window, event)
        assert not event.isAccepted()

    def test_close_accepted(self, main_window, monkeypatch):
        monkeypatch.setattr(
            QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.Yes
        )

        from PySide6.QtGui import QCloseEvent

        event = QCloseEvent()
        MainWindow.closeEvent(main_window, event)
        assert event.isAccepted()
