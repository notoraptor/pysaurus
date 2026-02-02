"""
Tests for PySide6 video widgets.

Tests VideoCard and VideoListItem widgets with mock data.
"""

import pytest
from PySide6.QtCore import Qt

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

        assert card.title_label.text() == "Test Video"

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
        assert "Test Video" in title_text

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
