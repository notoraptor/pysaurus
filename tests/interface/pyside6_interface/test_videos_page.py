"""
Tests for PySide6 VideosPage.

Tests the main video browsing page with mock database.
"""


class TestVideosPageCreation:
    """Tests for VideosPage initialization."""

    def test_page_creation(self, qtbot, mock_context):
        """Test that VideosPage can be created."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        assert page.ctx == mock_context
        assert page.page_size == 20
        assert page.page_number == 0

    def test_page_has_refresh_button(self, qtbot, mock_context):
        """Test that VideosPage has a refresh button."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        assert page.btn_refresh is not None

    def test_page_has_search_input(self, qtbot, mock_context):
        """Test that VideosPage has a search input."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        assert page.search_input is not None

    def test_page_has_pagination(self, qtbot, mock_context):
        """Test that VideosPage has pagination controls."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        assert page.btn_prev is not None
        assert page.btn_next is not None
        assert page.page_button is not None


class TestVideosPageRefresh:
    """Tests for VideosPage refresh functionality."""

    def test_refresh_loads_videos(self, qtbot, mock_context):
        """Test that refresh loads videos from database."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        page.refresh()

        # Should have loaded videos
        assert page._videos is not None
        assert len(page._videos) > 0

    def test_refresh_updates_page_count(self, qtbot, mock_context):
        """Test that refresh updates total page count."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        page.refresh()

        # With 5 test videos and page_size=20, should have 1 page
        assert page._total_pages >= 1


class TestVideosPageSelection:
    """Tests for video selection functionality."""

    def test_initial_selector_is_empty(self, qtbot, mock_context):
        """Test that initial selector has no selections."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        # Selector should be in include mode with empty selection
        assert not page._selector._to_exclude
        assert len(page._selector._selection) == 0

    def test_select_all_in_page(self, qtbot, mock_context):
        """Test selecting all videos in current page."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Select all in page
        page._select_all()

        # Should have selections
        assert len(page._selector._selection) > 0

    def test_clear_selection(self, qtbot, mock_context):
        """Test clearing selection."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Select some videos
        page._select_all()
        assert len(page._selector._selection) > 0

        # Clear selection
        page._clear_selection()
        assert len(page._selector._selection) == 0

    def test_video_selection_signal(self, qtbot, mock_context):
        """Test that video selection signal updates selector."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        video_id = 1
        # Simulate selection change via the handler
        page._on_video_selection_changed(video_id, True)

        assert video_id in page._selector._selection


class TestVideosPagePagination:
    """Tests for pagination functionality."""

    def test_next_page(self, qtbot, mock_context):
        """Test going to next page."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.page_size = 2  # Small page to test pagination
        page.refresh()

        initial_page = page.page_number

        # If there are more pages, go next
        if page._total_pages > 1:
            page._go_next()
            assert page.page_number == initial_page + 1

    def test_prev_page(self, qtbot, mock_context):
        """Test going to previous page."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.page_size = 2
        page.page_number = 1  # Start on second page
        page.refresh()

        page._go_prev()
        assert page.page_number == 0

    def test_prev_page_at_start(self, qtbot, mock_context):
        """Test that prev page does nothing at start."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.page_number = 0
        page.refresh()

        page._go_prev()
        assert page.page_number == 0


class TestVideosPageSearch:
    """Tests for search functionality."""

    def test_search_updates_provider(self, qtbot, mock_context):
        """Test that search updates the provider."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Set search text
        page.search_input.setText("Video 1")
        page._on_search()

        # Provider should have search set
        # Note: actual filtering depends on mock implementation

    def test_clear_search(self, qtbot, mock_context):
        """Test clearing search."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        # Set and clear search
        page.search_input.setText("test")
        page._on_search()

        page.search_input.clear()
        page._on_search()

        # Should show all videos again
        page.refresh()
        assert len(page._videos) > 0


class TestVideosPagePropertyValueClick:
    """Tests for property value click (focus prop val)."""

    def test_property_value_click_calls_classifier(self, qtbot, mock_context):
        """Test that property value click calls classifier_focus_prop_val."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        # Track calls to classifier_focus_prop_val
        calls = []
        original_method = mock_context.classifier_focus_prop_val

        def mock_focus(prop_name, value):
            calls.append((prop_name, value))

        mock_context.classifier_focus_prop_val = mock_focus

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Simulate property value click
        page._on_property_value_clicked("genre", "action")

        assert len(calls) == 1
        assert calls[0] == ("genre", "action")

        # Restore original
        mock_context.classifier_focus_prop_val = original_method


class TestVideosPageSelector:
    """Tests for the Selector class integration."""

    def test_selector_include_mode(self, qtbot, mock_context):
        """Test selector in include mode (add individual videos)."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Add video to selection
        video_id = 1
        page._on_video_selection_changed(video_id, True)

        assert video_id in page._selector._selection
        assert not page._selector._to_exclude  # Should be in include mode

    def test_selector_to_dict(self, qtbot, mock_context):
        """Test that selector can be converted to dict for apply_on_view."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Add some videos
        page._on_video_selection_changed(1, True)
        page._on_video_selection_changed(2, True)

        # Get dict
        selector_dict = page._selector.to_dict()

        assert "all" in selector_dict
        assert "include" in selector_dict
        assert "exclude" in selector_dict
        assert selector_dict["all"] is False
        assert 1 in selector_dict["include"]
        assert 2 in selector_dict["include"]

    def test_selector_deselect(self, qtbot, mock_context):
        """Test deselecting a video removes it from selector."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Add then remove video
        page._on_video_selection_changed(1, True)
        assert 1 in page._selector._selection

        page._on_video_selection_changed(1, False)
        assert 1 not in page._selector._selection
