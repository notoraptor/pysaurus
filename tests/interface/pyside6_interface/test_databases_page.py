"""
Tests for PySide6 DatabasesPage.

Tests the database selection and creation page.
"""

import pytest
from PySide6.QtCore import Qt


class TestDatabasesPageCreation:
    """Tests for DatabasesPage initialization."""

    def test_page_creation(self, qtbot, mock_context):
        """Test that DatabasesPage can be created."""
        from pysaurus.interface.pyside6.pages.databases_page import DatabasesPage

        page = DatabasesPage(mock_context)
        qtbot.addWidget(page)

        assert page.ctx == mock_context

    def test_page_has_database_list(self, qtbot, mock_context):
        """Test that page shows existing databases."""
        from pysaurus.interface.pyside6.pages.databases_page import DatabasesPage

        page = DatabasesPage(mock_context)
        qtbot.addWidget(page)

        # Should have database widgets for each database name
        assert len(page._db_widgets) == 2  # test_database, another_database

    def test_page_has_create_form(self, qtbot, mock_context):
        """Test that page has create database form."""
        from pysaurus.interface.pyside6.pages.databases_page import DatabasesPage

        page = DatabasesPage(mock_context)
        qtbot.addWidget(page)

        assert page.name_input is not None
        assert page.sources_list is not None
        assert page.btn_create is not None


class TestDatabaseItemWidget:
    """Tests for DatabaseItemWidget."""

    def test_widget_creation(self, qtbot):
        """Test that DatabaseItemWidget can be created."""
        from pysaurus.interface.pyside6.pages.databases_page import DatabaseItemWidget

        widget = DatabaseItemWidget("test_db")
        qtbot.addWidget(widget)

        assert widget.name == "test_db"
        assert widget.name_label.text() == "test_db"

    def test_widget_expand_collapse(self, qtbot):
        """Test widget expand/collapse functionality."""
        from pysaurus.interface.pyside6.pages.databases_page import DatabaseItemWidget

        widget = DatabaseItemWidget("test_db")
        qtbot.addWidget(widget)

        # Initially collapsed
        assert not widget._expanded
        # Note: Use isVisibleTo instead of isVisible because parent may not be shown
        assert not widget.buttons_widget.isVisibleTo(widget)

        # Expand
        widget.toggle_expanded()
        assert widget._expanded
        # After expanding, buttons_widget should be set to visible
        assert widget.buttons_widget.isVisibleTo(widget)

        # Collapse
        widget.collapse()
        assert not widget._expanded
        assert not widget.buttons_widget.isVisibleTo(widget)

    def test_widget_open_signal(self, qtbot):
        """Test that open button emits signal."""
        from pysaurus.interface.pyside6.pages.databases_page import DatabaseItemWidget

        widget = DatabaseItemWidget("test_db")
        qtbot.addWidget(widget)

        signals = []
        widget.open_clicked.connect(lambda name, update: signals.append((name, update)))

        # Expand and click open
        widget.toggle_expanded()
        widget.btn_open.click()

        assert len(signals) == 1
        assert signals[0] == ("test_db", False)

    def test_widget_update_signal(self, qtbot):
        """Test that update button emits signal with update=True."""
        from pysaurus.interface.pyside6.pages.databases_page import DatabaseItemWidget

        widget = DatabaseItemWidget("test_db")
        qtbot.addWidget(widget)

        signals = []
        widget.open_clicked.connect(lambda name, update: signals.append((name, update)))

        widget.toggle_expanded()
        widget.btn_update.click()

        assert len(signals) == 1
        assert signals[0] == ("test_db", True)

    def test_widget_delete_signal(self, qtbot):
        """Test that delete button emits signal."""
        from pysaurus.interface.pyside6.pages.databases_page import DatabaseItemWidget

        widget = DatabaseItemWidget("test_db")
        qtbot.addWidget(widget)

        signals = []
        widget.delete_clicked.connect(lambda name: signals.append(name))

        widget.toggle_expanded()
        widget.btn_delete.click()

        assert len(signals) == 1
        assert signals[0] == "test_db"


class TestDatabasesPageSignals:
    """Tests for DatabasesPage signals."""

    def test_database_opening_signal(self, qtbot, mock_context):
        """Test that opening a database emits signal."""
        from pysaurus.interface.pyside6.pages.databases_page import DatabasesPage

        page = DatabasesPage(mock_context)
        qtbot.addWidget(page)

        signals = []
        page.database_opening.connect(lambda name, update: signals.append((name, update)))

        # Find first database widget and trigger open
        if page._db_widgets:
            page._on_db_open("test_database", False)

            assert len(signals) == 1
            assert signals[0] == ("test_database", False)

    def test_database_creating_signal(self, qtbot, mock_context, monkeypatch):
        """Test that creating a database emits signal."""
        from pysaurus.interface.pyside6.pages.databases_page import DatabasesPage
        from PySide6.QtWidgets import QMessageBox

        page = DatabasesPage(mock_context)
        qtbot.addWidget(page)

        # Mock QMessageBox to auto-accept
        monkeypatch.setattr(
            QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes
        )

        signals = []
        page.database_creating.connect(
            lambda name, folders, update: signals.append((name, folders, update))
        )

        # Fill form
        page.name_input.setText("new_database")
        page.sources_list.addItem("📁 /test/folder")

        # Click create
        page.btn_create.click()

        assert len(signals) == 1
        assert signals[0][0] == "new_database"
        assert "/test/folder" in signals[0][1][0]
        assert signals[0][2] is True  # update=True


class TestDatabasesPageValidation:
    """Tests for form validation."""

    def test_create_without_name_shows_warning(self, qtbot, mock_context, monkeypatch):
        """Test that creating without name shows warning."""
        from pysaurus.interface.pyside6.pages.databases_page import DatabasesPage
        from PySide6.QtWidgets import QMessageBox

        page = DatabasesPage(mock_context)
        qtbot.addWidget(page)

        warnings = []
        monkeypatch.setattr(
            QMessageBox, "warning", lambda *args, **kwargs: warnings.append(args)
        )

        # Try to create without name
        page.btn_create.click()

        assert len(warnings) == 1
        assert "name" in warnings[0][2].lower()

    def test_create_without_sources_shows_warning(self, qtbot, mock_context, monkeypatch):
        """Test that creating without sources shows warning."""
        from pysaurus.interface.pyside6.pages.databases_page import DatabasesPage
        from PySide6.QtWidgets import QMessageBox

        page = DatabasesPage(mock_context)
        qtbot.addWidget(page)

        warnings = []
        monkeypatch.setattr(
            QMessageBox, "warning", lambda *args, **kwargs: warnings.append(args)
        )

        # Set name but no sources
        page.name_input.setText("test")
        page.btn_create.click()

        assert len(warnings) == 1
        assert "source" in warnings[0][2].lower()


class TestDatabasesPageRefresh:
    """Tests for refresh functionality."""

    def test_refresh_updates_list(self, qtbot, mock_context):
        """Test that refresh updates the database list."""
        from pysaurus.interface.pyside6.pages.databases_page import DatabasesPage

        page = DatabasesPage(mock_context)
        qtbot.addWidget(page)

        initial_count = len(page._db_widgets)

        # Add a database name
        mock_context.application._database_names.append("third_database")
        page.refresh()

        assert len(page._db_widgets) == initial_count + 1
