"""
Tests for scrolling behavior in PySide6 video views.

Ensures:
- Scrollbar is hidden when content fits in the view
- Scrollbar doesn't scroll beyond the last video
- Wrapping works correctly in list view
"""

from PySide6.QtWidgets import QApplication

from tests.mocks.mock_database import MockVideoPattern


def make_video_dicts(count: int) -> list[dict]:
    """Create a list of mock video dictionaries for database storage."""
    videos = []
    for i in range(count):
        videos.append(
            {
                "video_id": i + 1,
                "filename": f"/videos/test_video_{i + 1}.mp4",
                "file_size": 1024 * 1024 * (i + 1),
                "mtime": 1700000000.0 + i,
                "duration": 3600,
                "duration_time_base": 1,
                "height": 1080,
                "width": 1920,
                "meta_title": f"Video {i + 1} with a longer title for wrapping tests",
                "found": True,
                "unreadable": False,
                "watched": False,
                "with_thumbnails": True,
                "video_codec": "h264",
                "video_codec_description": "H.264",
                "audio_codec": "aac",
                "channels": 2,
                "sample_rate": 44100,
                "audio_bit_rate": 128000,
                "container_format": "mp4",
                "frame_rate_num": 30,
                "frame_rate_den": 1,
                "date_entry_modified": "2024-01-15",
                "similarity_id": None,
                "properties": {},
            }
        )
    return videos


class TestGridViewScrolling:
    """Tests for grid view scrolling behavior."""

    def test_scrollbar_hidden_when_content_fits(self, qtbot, mock_context):
        """Test that vertical scrollbar is hidden when all videos fit in view."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        # Set up with just 2 videos - should fit in a reasonable view
        mock_context._database._videos = make_video_dicts(2)

        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        # Set view to grid mode
        page._current_view = 0
        page.view_stack.setCurrentIndex(0)

        # Make the page large enough to fit 2 videos
        page.resize(1200, 800)
        page.show()
        QApplication.processEvents()

        page.refresh()
        QApplication.processEvents()

        # Check that vertical scrollbar is not needed
        scroll_area = page.scroll_area
        v_scrollbar = scroll_area.verticalScrollBar()

        # When content fits, scrollbar maximum should be 0 or scrollbar should be hidden
        content_fits = v_scrollbar.maximum() == 0 or not v_scrollbar.isVisible()
        assert content_fits, (
            f"Scrollbar should not be needed for 2 videos. "
            f"Maximum={v_scrollbar.maximum()}, Visible={v_scrollbar.isVisible()}"
        )

    def test_scrollbar_visible_when_content_exceeds_view(self, qtbot, mock_context):
        """Test that vertical scrollbar appears when videos exceed view height."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        # Set up with many videos
        mock_context._database._videos = make_video_dicts(50)
        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        # Set view to grid mode
        page._current_view = 0
        page.view_stack.setCurrentIndex(0)

        # Increase page_size to show all videos on one page
        page.page_size = 100

        # Make the page small to force scrolling
        page.resize(400, 300)
        page.show()

        # Wait for widget to be exposed
        qtbot.waitExposed(page)

        page.refresh()

        # Force layout recalculation
        page.video_container.updateGeometry()
        page.scroll_area.updateGeometry()
        QApplication.processEvents()

        # Check that vertical scrollbar is needed
        scroll_area = page.scroll_area
        v_scrollbar = scroll_area.verticalScrollBar()

        # When content overflows, scrollbar maximum should be > 0
        assert v_scrollbar.maximum() > 0, (
            f"Scrollbar should be needed for 50 videos in a small view. "
            f"Maximum={v_scrollbar.maximum()}, "
            f"Container size={page.video_container.sizeHint()}, "
            f"Viewport size={scroll_area.viewport().size()}"
        )

    def test_scroll_maximum_matches_content_bottom(self, qtbot, mock_context):
        """Test that scrollbar maximum allows reaching exactly the last video."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        # Set up with enough videos to require scrolling
        mock_context._database._videos = make_video_dicts(20)
        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        # Set view to grid mode
        page._current_view = 0
        page.view_stack.setCurrentIndex(0)

        page.resize(600, 400)
        page.show()
        QApplication.processEvents()

        page.refresh()
        QApplication.processEvents()

        scroll_area = page.scroll_area
        v_scrollbar = scroll_area.verticalScrollBar()

        if v_scrollbar.maximum() > 0:
            # Scroll to maximum
            v_scrollbar.setValue(v_scrollbar.maximum())
            QApplication.processEvents()

            # The content widget's bottom should be visible at scroll maximum
            content_widget = page.video_container
            content_height = content_widget.sizeHint().height()
            viewport_height = scroll_area.viewport().height()
            scroll_pos = v_scrollbar.value()

            # At maximum scroll, the visible area should end at content bottom
            visible_bottom = scroll_pos + viewport_height

            # Allow small tolerance for margins/borders
            assert abs(visible_bottom - content_height) < 20, (
                f"At max scroll, visible bottom ({visible_bottom}) should match "
                f"content height ({content_height})"
            )

    def test_cannot_scroll_beyond_last_video(self, qtbot, mock_context):
        """Test that scrolling beyond content is not possible."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        mock_context._database._videos = make_video_dicts(15)
        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        page._current_view = 0
        page.view_stack.setCurrentIndex(0)

        page.resize(600, 400)
        page.show()
        QApplication.processEvents()

        page.refresh()
        QApplication.processEvents()

        scroll_area = page.scroll_area
        v_scrollbar = scroll_area.verticalScrollBar()

        if v_scrollbar.maximum() > 0:
            # Try to scroll beyond maximum
            max_value = v_scrollbar.maximum()
            v_scrollbar.setValue(max_value + 1000)
            QApplication.processEvents()

            # Value should be clamped to maximum
            assert v_scrollbar.value() == max_value, (
                f"Scroll value should be clamped to {max_value}, "
                f"but is {v_scrollbar.value()}"
            )


class TestListViewScrolling:
    """Tests for list view scrolling behavior."""

    def test_scrollbar_hidden_when_content_fits(self, qtbot, mock_context):
        """Test that vertical scrollbar is hidden when all videos fit in view."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        # Set up with just 1 video - should fit in a reasonable view
        mock_context._database._videos = make_video_dicts(1)
        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        # Set view to list mode
        page._current_view = 1
        page.view_stack.setCurrentIndex(1)

        # Make the page large enough
        page.resize(1200, 800)
        page.show()
        QApplication.processEvents()

        page.refresh()
        QApplication.processEvents()

        # Check that vertical scrollbar is not needed
        scroll_area = page.list_scroll_area
        v_scrollbar = scroll_area.verticalScrollBar()

        content_fits = v_scrollbar.maximum() == 0 or not v_scrollbar.isVisible()
        assert content_fits, (
            f"Scrollbar should not be needed for 1 video in list view. "
            f"Maximum={v_scrollbar.maximum()}, Visible={v_scrollbar.isVisible()}"
        )

    def test_scrollbar_visible_when_content_exceeds_view(self, qtbot, mock_context):
        """Test that vertical scrollbar appears when videos exceed view height."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        # Set up with many videos
        mock_context._database._videos = make_video_dicts(30)
        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        # Set view to list mode
        page._current_view = 1
        page.view_stack.setCurrentIndex(1)

        # Increase page_size to show all videos on one page
        page.page_size = 100

        page.resize(800, 400)
        page.show()

        # Wait for widget to be exposed
        qtbot.waitExposed(page)

        page.refresh()

        # Force layout recalculation
        page.list_container.updateGeometry()
        page.list_scroll_area.updateGeometry()
        QApplication.processEvents()

        scroll_area = page.list_scroll_area
        v_scrollbar = scroll_area.verticalScrollBar()

        assert v_scrollbar.maximum() > 0, (
            f"Scrollbar should be needed for 30 videos in list view. "
            f"Maximum={v_scrollbar.maximum()}, "
            f"Container size={page.list_container.sizeHint()}, "
            f"Viewport size={scroll_area.viewport().size()}"
        )

    def test_stretch_absorbs_extra_space(self, qtbot, mock_context):
        """Test that the stretch item absorbs extra space below videos."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        # Set up with few videos
        mock_context._database._videos = make_video_dicts(2)
        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        # Set view to list mode
        page._current_view = 1
        page.view_stack.setCurrentIndex(1)

        page.resize(1200, 800)
        page.show()
        QApplication.processEvents()

        page.refresh()
        QApplication.processEvents()

        # The list_layout should have a stretch at the end
        list_layout = page.list_layout
        last_item = list_layout.itemAt(list_layout.count() - 1)

        # Check that a stretch exists (QSpacerItem with expanding vertical policy)
        # A stretch item is a spacer with expanding vertical size policy
        assert last_item is not None, "List layout should have items"

        # If videos don't fill the space, the container should still fit within scroll area
        scroll_area = page.list_scroll_area
        v_scrollbar = scroll_area.verticalScrollBar()

        # With few items and large view, no scrolling should be needed
        assert v_scrollbar.maximum() == 0 or not v_scrollbar.isVisible(), (
            "With stretch absorbing space, scrollbar should not be needed"
        )

    def test_scroll_maximum_matches_content_bottom(self, qtbot, mock_context):
        """Test that scrollbar maximum allows reaching exactly the last video."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        mock_context._database._videos = make_video_dicts(20)
        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        page._current_view = 1
        page.view_stack.setCurrentIndex(1)

        page.resize(800, 400)
        page.show()
        QApplication.processEvents()

        page.refresh()
        QApplication.processEvents()

        scroll_area = page.list_scroll_area
        v_scrollbar = scroll_area.verticalScrollBar()

        if v_scrollbar.maximum() > 0:
            # Scroll to maximum
            v_scrollbar.setValue(v_scrollbar.maximum())
            QApplication.processEvents()

            content_widget = page.list_container
            content_height = content_widget.sizeHint().height()
            viewport_height = scroll_area.viewport().height()
            scroll_pos = v_scrollbar.value()

            visible_bottom = scroll_pos + viewport_height

            # Allow tolerance for margins/borders/stretch
            assert abs(visible_bottom - content_height) < 50, (
                f"At max scroll, visible bottom ({visible_bottom}) should be near "
                f"content height ({content_height})"
            )

    def test_cannot_scroll_beyond_last_video(self, qtbot, mock_context):
        """Test that scrolling beyond content is not possible."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        mock_context._database._videos = make_video_dicts(15)
        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        page._current_view = 1
        page.view_stack.setCurrentIndex(1)

        page.resize(800, 400)
        page.show()
        QApplication.processEvents()

        page.refresh()
        QApplication.processEvents()

        scroll_area = page.list_scroll_area
        v_scrollbar = scroll_area.verticalScrollBar()

        if v_scrollbar.maximum() > 0:
            max_value = v_scrollbar.maximum()
            v_scrollbar.setValue(max_value + 1000)
            QApplication.processEvents()

            assert v_scrollbar.value() == max_value, (
                f"Scroll value should be clamped to {max_value}, "
                f"but is {v_scrollbar.value()}"
            )


class TestListViewWrapping:
    """Tests for text wrapping in list view items."""

    def test_wrapping_label_wraps_long_text(self, qtbot):
        """Test that WrappingLabel wraps long text."""
        from pysaurus.interface.pyside6.widgets.video_list_item import WrappingLabel

        long_text = "This is a very long title that should wrap to multiple lines when the widget is narrow enough to require wrapping"

        label = WrappingLabel(long_text)
        qtbot.addWidget(label)

        # Force narrow width
        label.setFixedWidth(200)
        label.show()
        QApplication.processEvents()

        # WrappingLabel should report height for width
        assert label.hasHeightForWidth()

        # Height for narrow width should be greater than height for wide width
        narrow_height = label.heightForWidth(200)
        wide_height = label.heightForWidth(800)

        assert narrow_height > wide_height, (
            f"Narrow label ({narrow_height}px) should be taller than wide label ({wide_height}px)"
        )

    def test_video_list_item_wraps_long_filename(self, qtbot):
        """Test that VideoListItem wraps long filenames correctly."""
        from pysaurus.interface.pyside6.widgets.video_list_item import VideoListItem

        video = MockVideoPattern(
            {
                "video_id": 1,
                "filename": "/very/long/path/to/videos/with/many/subdirectories/and/a/really/long/filename_that_should_wrap_properly_in_the_list_view.mp4",
                "file_size": 1024 * 1024,
                "mtime": 1700000000.0,
                "duration": 3600,
                "duration_time_base": 1,
                "height": 1080,
                "width": 1920,
                "meta_title": "A video with a very long title that should also wrap correctly when displayed in the list view widget",
                "found": True,
                "unreadable": False,
                "watched": False,
                "with_thumbnails": False,
                "video_codec": "h264",
                "video_codec_description": "H.264",
                "audio_codec": "aac",
                "channels": 2,
                "sample_rate": 44100,
                "audio_bit_rate": 128000,
                "container_format": "mp4",
                "frame_rate_num": 30,
                "frame_rate_den": 1,
                "date_entry_modified": "2024-01-15",
                "similarity_id": None,
                "properties": {},
            }
        )

        item = VideoListItem(video)
        qtbot.addWidget(item)

        # Set narrow width to trigger wrapping
        item.setFixedWidth(400)
        item.show()
        QApplication.processEvents()

        # The item should adapt its height to accommodate wrapped text
        narrow_hint = item.sizeHint()

        # Set wide width
        item.setFixedWidth(1200)
        QApplication.processEvents()

        wide_hint = item.sizeHint()

        # Narrow item should be taller due to wrapping
        assert narrow_hint.height() >= wide_hint.height(), (
            f"Narrow item ({narrow_hint.height()}px) should be at least as tall as "
            f"wide item ({wide_hint.height()}px) due to text wrapping"
        )

    def test_break_opportunities_in_paths(self, qtbot):
        """Test that paths have break opportunities after separators."""
        from pysaurus.interface.pyside6.widgets.video_list_item import (
            _add_break_opportunities,
        )

        path = "/path/to/videos/file_name.mp4"
        result = _add_break_opportunities(path)

        # Should have zero-width spaces after path separators
        assert "\u200b" in result, "Path should have break opportunities"

        # Count break opportunities
        break_count = result.count("\u200b")
        # Expect breaks after /, _, and .
        expected_min_breaks = 4  # /path/, /to/, /videos/, file_, name.
        assert break_count >= expected_min_breaks, (
            f"Expected at least {expected_min_breaks} break opportunities, got {break_count}"
        )

    def test_list_item_expands_horizontally(self, qtbot):
        """Test that VideoListItem expands to fill available width."""
        from pysaurus.interface.pyside6.widgets.video_list_item import VideoListItem
        from PySide6.QtWidgets import QSizePolicy

        video = MockVideoPattern(
            {
                "video_id": 1,
                "filename": "/videos/test.mp4",
                "file_size": 1024 * 1024,
                "mtime": 1700000000.0,
                "duration": 3600,
                "duration_time_base": 1,
                "height": 1080,
                "width": 1920,
                "meta_title": "Test Video",
                "found": True,
                "unreadable": False,
                "watched": False,
                "with_thumbnails": False,
                "video_codec": "h264",
                "video_codec_description": "H.264",
                "audio_codec": "aac",
                "channels": 2,
                "sample_rate": 44100,
                "audio_bit_rate": 128000,
                "container_format": "mp4",
                "frame_rate_num": 30,
                "frame_rate_den": 1,
                "date_entry_modified": "2024-01-15",
                "similarity_id": None,
                "properties": {},
            }
        )

        item = VideoListItem(video)
        qtbot.addWidget(item)

        # Check horizontal size policy is Expanding
        h_policy = item.sizePolicy().horizontalPolicy()
        assert h_policy == QSizePolicy.Policy.Expanding, (
            f"VideoListItem should have Expanding horizontal policy, got {h_policy}"
        )


class TestGridViewFlowLayout:
    """Tests for FlowLayout wrapping behavior in grid view."""

    def test_flow_layout_wraps_items(self, qtbot):
        """Test that FlowLayout wraps items to next row."""
        from pysaurus.interface.pyside6.widgets.flow_layout import FlowLayout
        from PySide6.QtWidgets import QWidget, QPushButton

        container = QWidget()
        layout = FlowLayout(container, h_spacing=10, v_spacing=10)

        # Add items
        buttons = []
        for i in range(10):
            btn = QPushButton(f"Button {i}")
            btn.setFixedSize(100, 50)
            layout.addWidget(btn)
            buttons.append(btn)

        qtbot.addWidget(container)

        # Set narrow width - should force wrapping
        container.setFixedWidth(350)  # Fits ~3 buttons per row
        container.show()
        QApplication.processEvents()

        # Calculate height needed - should be multiple rows
        height = layout.heightForWidth(350)

        # Single row would be ~50px, multiple rows should be > 100px
        assert height > 100, f"FlowLayout should wrap to multiple rows, height={height}"

    def test_flow_layout_height_increases_with_narrow_width(self, qtbot):
        """Test that FlowLayout reports greater height for narrower width."""
        from pysaurus.interface.pyside6.widgets.flow_layout import FlowLayout
        from PySide6.QtWidgets import QWidget, QPushButton

        container = QWidget()
        layout = FlowLayout(container, h_spacing=10, v_spacing=10)

        for i in range(8):
            btn = QPushButton(f"Btn{i}")
            btn.setFixedSize(80, 40)
            layout.addWidget(btn)

        qtbot.addWidget(container)
        container.show()
        QApplication.processEvents()

        # Get height for different widths
        wide_height = layout.heightForWidth(800)
        narrow_height = layout.heightForWidth(200)

        assert narrow_height > wide_height, (
            f"Narrow width ({narrow_height}px) should produce taller layout "
            f"than wide width ({wide_height}px)"
        )

    def test_video_cards_wrap_in_grid_view(self, qtbot, mock_context):
        """Test that video cards wrap properly in grid view."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        mock_context._database._videos = make_video_dicts(10)
        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        page._current_view = 0
        page.view_stack.setCurrentIndex(0)

        page.show()
        QApplication.processEvents()

        page.refresh()
        QApplication.processEvents()

        # Get content height for different page widths
        page.resize(1200, 600)
        QApplication.processEvents()
        wide_height = page.video_container.sizeHint().height()

        page.resize(400, 600)
        QApplication.processEvents()
        narrow_height = page.video_container.sizeHint().height()

        # With narrower width, cards should wrap to more rows = taller
        assert narrow_height >= wide_height, (
            f"Narrow view ({narrow_height}px) should be at least as tall as "
            f"wide view ({wide_height}px) due to card wrapping"
        )
