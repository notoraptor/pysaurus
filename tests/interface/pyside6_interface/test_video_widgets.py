"""
Tests for PySide6 video widgets.

Tests VideoCard and VideoListItem widgets with mock data.
"""

import pytest
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QEnterEvent

from tests.mocks.mock_database import MockVideoPattern


@pytest.fixture
def sample_video_data():
    """Sample video data for widget testing."""
    return {
        "video_id": 1,
        "filename": "/videos/test.mp4",
        "file_size": 104857600,
        "mtime": 1700000000.0,
        "duration": 3600000000,
        "duration_time_base": 1000000,
        "height": 1080,
        "width": 1920,
        "meta_title": "Test Video",
        "found": True,
        "unreadable": False,
        "watched": False,
        "with_thumbnails": False,
        "properties": {"genre": ["action", "comedy"], "rating": [8]},
    }


@pytest.fixture
def sample_video(sample_video_data):
    """Create a MockVideoPattern from sample data."""
    return MockVideoPattern(sample_video_data)


class TestVideoCard:
    """Tests for VideoCard widget."""

    def test_card_creation(self, qtbot, sample_video):
        """Test that VideoCard can be created with a video."""
        from pysaurus.interface.pyside6.widgets.video_card import VideoCard

        card = VideoCard(sample_video)
        qtbot.addWidget(card)

        assert card.video == sample_video
        assert card.video.video_id == 1

    def test_card_displays_title(self, qtbot, sample_video):
        """Test that VideoCard displays video title."""
        from pysaurus.interface.pyside6.widgets.video_card import VideoCard

        card = VideoCard(sample_video)
        qtbot.addWidget(card)

        assert card.title_label.text() == "test"

    def test_card_selection_via_checkbox(self, qtbot, sample_video):
        """Test that clicking checkbox toggles selection."""
        from pysaurus.interface.pyside6.widgets.video_card import VideoCard

        card = VideoCard(sample_video)
        qtbot.addWidget(card)

        # Initially not selected
        assert not card.selected
        assert not card.checkbox.isChecked()

        # Track signal emission
        signals_received = []
        card.selection_changed.connect(
            lambda vid, sel: signals_received.append((vid, sel))
        )

        # Click checkbox
        card.checkbox.setChecked(True)

        # Should be selected now
        assert card.selected
        assert card.checkbox.isChecked()

        # Signal should have been emitted
        assert len(signals_received) == 1
        assert signals_received[0] == (1, True)

    def test_card_selection_via_title_click(self, qtbot, sample_video):
        """Test that clicking title toggles checkbox."""
        from pysaurus.interface.pyside6.widgets.video_card import VideoCard

        card = VideoCard(sample_video)
        qtbot.addWidget(card)

        # Initially not selected
        assert not card.checkbox.isChecked()

        # Simulate title click
        card._on_title_clicked(None)

        # Should be checked now
        assert card.checkbox.isChecked()

        # Click again to uncheck
        card._on_title_clicked(None)
        assert not card.checkbox.isChecked()

    def test_card_programmatic_selection(self, qtbot, sample_video):
        """Test that setting selected property updates checkbox."""
        from pysaurus.interface.pyside6.widgets.video_card import VideoCard

        card = VideoCard(sample_video)
        qtbot.addWidget(card)

        # Set selection programmatically
        card.selected = True

        # Checkbox should be updated
        assert card.checkbox.isChecked()
        assert card.selected

        # Unset selection
        card.selected = False
        assert not card.checkbox.isChecked()
        assert not card.selected

    def test_card_click_does_not_toggle_selection(self, qtbot, sample_video):
        """Test that clicking card body does not toggle selection."""
        from pysaurus.interface.pyside6.widgets.video_card import VideoCard

        card = VideoCard(sample_video)
        qtbot.addWidget(card)

        # Track clicked signal, not selection_changed
        clicks = []
        card.clicked.connect(lambda vid, mods: clicks.append(vid))

        # Simulate mouse press on card body
        qtbot.mouseClick(card, Qt.MouseButton.LeftButton)

        # Should emit clicked signal
        assert len(clicks) == 1
        assert clicks[0] == 1

        # But selection should NOT change
        assert not card.selected

    def test_card_double_click_emits_signal(self, qtbot, sample_video):
        """Test that double-clicking card emits double_clicked signal."""
        from pysaurus.interface.pyside6.widgets.video_card import VideoCard

        card = VideoCard(sample_video)
        qtbot.addWidget(card)

        double_clicks = []
        card.double_clicked.connect(lambda vid: double_clicks.append(vid))

        qtbot.mouseDClick(card, Qt.MouseButton.LeftButton)

        assert len(double_clicks) == 1
        assert double_clicks[0] == 1

    def test_card_not_found_style(self, qtbot, sample_video_data):
        """Test that not-found videos have different style."""
        from pysaurus.interface.pyside6.widgets.video_card import VideoCard

        # Create not-found video
        sample_video_data["found"] = False
        video = MockVideoPattern(sample_video_data)

        card = VideoCard(video)
        qtbot.addWidget(card)

        # Should have yellow-ish background (check stylesheet contains #fffde7)
        stylesheet = card.styleSheet()
        assert "#fffde7" in stylesheet or "not found" in stylesheet.lower()


class TestVideoListItem:
    """Tests for VideoListItem widget."""

    def test_list_item_creation(self, qtbot, sample_video, prop_types):
        """Test that VideoListItem can be created."""
        from pysaurus.interface.pyside6.widgets.video_list_item import VideoListItem

        item = VideoListItem(sample_video, prop_types)
        qtbot.addWidget(item)

        assert item.video == sample_video

    def test_list_item_displays_title(self, qtbot, sample_video, prop_types):
        """Test that VideoListItem displays video title."""
        from pysaurus.interface.pyside6.widgets.video_list_item import VideoListItem

        item = VideoListItem(sample_video, prop_types)
        qtbot.addWidget(item)

        # title_label contains HTML-formatted text
        title_text = item.title_label.text()
        assert "test" in title_text

    def test_list_item_has_checkbox(self, qtbot, sample_video, prop_types):
        """Test that VideoListItem has a checkbox."""
        from pysaurus.interface.pyside6.widgets.video_list_item import VideoListItem

        item = VideoListItem(sample_video, prop_types)
        qtbot.addWidget(item)

        assert item.checkbox is not None

    def test_list_item_selection_via_checkbox(self, qtbot, sample_video, prop_types):
        """Test that checkbox toggles selection."""
        from pysaurus.interface.pyside6.widgets.video_list_item import VideoListItem

        item = VideoListItem(sample_video, prop_types)
        qtbot.addWidget(item)

        signals_received = []
        item.selection_changed.connect(
            lambda vid, sel: signals_received.append((vid, sel))
        )

        # Initially not selected
        assert not item.selected

        # Click checkbox
        item.checkbox.setChecked(True)

        assert item.selected
        assert len(signals_received) == 1
        assert signals_received[0] == (1, True)

    def test_list_item_property_value_click(self, qtbot, sample_video, prop_types):
        """Test that clicking property value emits signal."""
        from pysaurus.interface.pyside6.widgets.video_list_item import VideoListItem

        item = VideoListItem(sample_video, prop_types)
        qtbot.addWidget(item)

        # Track property_value_clicked signal
        clicks = []
        item.property_value_clicked.connect(
            lambda prop, val: clicks.append((prop, val))
        )

        # Simulate property value click
        item._on_property_value_clicked("genre", "action")

        assert len(clicks) == 1
        assert clicks[0] == ("genre", "action")

    def test_list_item_double_click(self, qtbot, sample_video, prop_types):
        """Test that double-clicking emits signal."""
        from pysaurus.interface.pyside6.widgets.video_list_item import VideoListItem

        item = VideoListItem(sample_video, prop_types)
        qtbot.addWidget(item)

        double_clicks = []
        item.double_clicked.connect(lambda vid: double_clicks.append(vid))

        qtbot.mouseDClick(item, Qt.MouseButton.LeftButton)

        assert len(double_clicks) == 1
        assert double_clicks[0] == 1


def _make_enter_event(widget):
    """Create an QEnterEvent for the given widget's center."""
    center = QPointF(widget.width() / 2, widget.height() / 2)
    return QEnterEvent(center, center, QPointF(widget.mapToGlobal(QPoint(0, 0))))


class TestVideoListItemHover:
    """Tests for VideoListItem hover and highlight behavior."""

    def _make_item(self, qtbot, sample_video, prop_types):
        from pysaurus.interface.pyside6.widgets.video_list_item import VideoListItem

        item = VideoListItem(sample_video, prop_types)
        qtbot.addWidget(item)
        item.resize(400, 120)
        return item

    def test_initial_state_no_hover_no_selection(self, qtbot, sample_video, prop_types):
        """Item starts with no hover and no selection."""
        item = self._make_item(qtbot, sample_video, prop_types)
        assert not item._hovered
        assert not item._selected
        assert "#ffffff" in item.styleSheet()

    def test_enter_sets_hover(self, qtbot, sample_video, prop_types):
        """enterEvent sets _hovered and applies hover style."""
        item = self._make_item(qtbot, sample_video, prop_types)
        item.enterEvent(_make_enter_event(item))
        assert item._hovered
        # Hover color for found videos: light blue
        assert "#f5f9ff" in item.styleSheet()

    def test_leave_clears_hover(self, qtbot, sample_video, prop_types):
        """leaveEvent clears _hovered and reverts to default style."""
        item = self._make_item(qtbot, sample_video, prop_types)
        item.enterEvent(_make_enter_event(item))
        assert item._hovered

        item.leaveEvent(QEvent(QEvent.Type.Leave))
        assert not item._hovered
        assert "#ffffff" in item.styleSheet()

    def test_hover_and_selected_have_different_colors(
        self, qtbot, sample_video, prop_types
    ):
        """Hover and selection styles must be visually distinct."""
        item = self._make_item(qtbot, sample_video, prop_types)

        # Get hover style
        item.enterEvent(_make_enter_event(item))
        hover_style = item.styleSheet()

        # Get selection style
        item.leaveEvent(QEvent(QEvent.Type.Leave))
        item.selected = True
        selected_style = item.styleSheet()

        assert hover_style != selected_style
        # Hover uses lighter blue
        assert "#f5f9ff" in hover_style
        # Selection uses stronger blue
        assert "#e3f2fd" in selected_style

    def test_selected_and_hovered_has_distinct_style(
        self, qtbot, sample_video, prop_types
    ):
        """Selected + hovered combines into a third distinct style."""
        item = self._make_item(qtbot, sample_video, prop_types)
        item.selected = True
        item.enterEvent(_make_enter_event(item))
        style = item.styleSheet()
        # Selected+hover uses darker blue
        assert "#d0e8fc" in style

    def test_context_menu_preserves_hover(self, qtbot, sample_video, prop_types):
        """Hover stays active during context menu (leaveEvent is ignored)."""
        item = self._make_item(qtbot, sample_video, prop_types)

        # Simulate hover
        item.enterEvent(_make_enter_event(item))
        assert item._hovered

        # Simulate context menu opening: set flag and fire leaveEvent
        item._context_menu_open = True
        item.leaveEvent(QEvent(QEvent.Type.Leave))

        # Hover should be preserved
        assert item._hovered

        item._context_menu_open = False

    def test_context_menu_clears_hover_when_cursor_leaves(
        self, qtbot, sample_video, prop_types
    ):
        """After context menu closes, hover clears if cursor is outside."""
        from unittest.mock import patch

        from PySide6.QtGui import QCursor

        item = self._make_item(qtbot, sample_video, prop_types)
        item.enterEvent(_make_enter_event(item))
        assert item._hovered

        # Intercept the signal to avoid needing a real context menu
        signals = []
        item.context_menu_requested.connect(lambda *args: signals.append(args))

        # Simulate cursor far outside the widget
        far_away = item.mapToGlobal(QPoint(-1000, -1000))
        with patch.object(QCursor, "pos", return_value=far_away):
            from PySide6.QtGui import QContextMenuEvent

            event = QContextMenuEvent(
                QContextMenuEvent.Reason.Mouse,
                QPoint(10, 10),
                item.mapToGlobal(QPoint(10, 10)),
            )
            item.contextMenuEvent(event)

        # Hover should be cleared
        assert not item._hovered
        assert "#ffffff" in item.styleSheet()

    def test_context_menu_keeps_hover_when_cursor_stays(
        self, qtbot, sample_video, prop_types
    ):
        """After context menu closes, hover stays if cursor is still over widget."""
        from unittest.mock import patch

        from PySide6.QtGui import QCursor

        item = self._make_item(qtbot, sample_video, prop_types)
        item.enterEvent(_make_enter_event(item))

        signals = []
        item.context_menu_requested.connect(lambda *args: signals.append(args))

        # Simulate cursor still over the widget center
        center = item.mapToGlobal(QPoint(item.width() // 2, item.height() // 2))
        with patch.object(QCursor, "pos", return_value=center):
            from PySide6.QtGui import QContextMenuEvent

            event = QContextMenuEvent(
                QContextMenuEvent.Reason.Mouse,
                QPoint(10, 10),
                item.mapToGlobal(QPoint(10, 10)),
            )
            item.contextMenuEvent(event)

        assert item._hovered
        assert "#f5f9ff" in item.styleSheet()

    def test_not_found_video_hover_style(self, qtbot, sample_video_data, prop_types):
        """Not-found videos have distinct hover color (orange, not blue)."""
        from pysaurus.interface.pyside6.widgets.video_list_item import VideoListItem

        sample_video_data["found"] = False
        video = MockVideoPattern(sample_video_data)

        item = VideoListItem(video, prop_types)
        qtbot.addWidget(item)
        item.resize(400, 120)

        item.enterEvent(_make_enter_event(item))
        style = item.styleSheet()
        # Not-found hover: orange
        assert "#ffecb3" in style
