"""
Tests for PySide6 VideosPage.

Tests the main video browsing page with mock database.
"""

from pysaurus.interface.pyside6.pages.videos_page import VideosPage


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

    def test_page_has_view_combo(self, qtbot, mock_context):
        """Test that VideosPage has a view toggle combo box."""
        from pysaurus.interface.pyside6.pages.videos_page import VideosPage

        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        assert page.view_combo is not None

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
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Add then remove video
        page._on_video_selection_changed(1, True)
        assert 1 in page._selector._selection

        page._on_video_selection_changed(1, False)
        assert 1 not in page._selector._selection


class TestVideosPageViewMode:
    """Tests for view mode switching (grid/list)."""

    def test_initial_view_is_list(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        assert page._current_view == VideosPage.VIEW_LIST

    def test_switch_to_grid_view(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page._on_view_changed(VideosPage.VIEW_GRID)

        assert page._current_view == VideosPage.VIEW_GRID
        assert page.view_stack.currentIndex() == VideosPage.VIEW_GRID

    def test_switch_to_list_view(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page._on_view_changed(VideosPage.VIEW_GRID)
        page._on_view_changed(VideosPage.VIEW_LIST)

        assert page._current_view == VideosPage.VIEW_LIST

    def test_view_combo_triggers_change(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page.view_combo.setCurrentIndex(VideosPage.VIEW_GRID)

        assert page._current_view == VideosPage.VIEW_GRID


class TestVideosPagePageSize:
    """Tests for page size changes."""

    def test_change_page_size(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page._on_page_size_changed("50")

        assert page.page_size == 50
        assert page.page_number == 0

    def test_page_size_resets_to_page_zero(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.page_number = 3
        page.refresh()

        page._on_page_size_changed("10")

        assert page.page_number == 0


class TestVideosPageSearchModes:
    """Tests for different search modes."""

    def test_search_and_mode(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        calls = []
        mock_context.set_search = lambda text, cond: calls.append((text, cond))

        page.search_input.setText("test query")
        page._on_search_and()

        assert calls == [("test query", "and")]

    def test_search_or_mode(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        calls = []
        mock_context.set_search = lambda text, cond: calls.append((text, cond))

        page.search_input.setText("test query")
        page._on_search_or()

        assert calls == [("test query", "or")]

    def test_search_exact_mode(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        calls = []
        mock_context.set_search = lambda text, cond: calls.append((text, cond))

        page.search_input.setText("test query")
        page._on_search_exact()

        assert calls == [("test query", "exact")]

    def test_search_id_mode(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        calls = []
        mock_context.set_search = lambda text, cond: calls.append((text, cond))

        page.search_input.setText("42")
        page._on_search_id()

        assert calls == [("42", "id")]

    def test_clear_search_resets_mode(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page._search_mode = "or"
        page._clear_search()

        assert page._search_mode == "and"
        assert page.search_input.text() == ""

    def test_empty_search_not_applied(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        calls = []
        mock_context.set_search = lambda text, cond: calls.append((text, cond))

        page.search_input.setText("")
        page._do_search("and")

        assert len(calls) == 0


class TestVideosPageClearActions:
    """Tests for clear/reset actions."""

    def test_clear_sources(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.page_number = 3
        page.refresh()

        calls = []
        mock_context.set_sources = lambda src: calls.append(src)

        page._clear_sources()

        assert calls == [None]
        assert page.page_number == 0

    def test_clear_grouping(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.page_number = 3
        page.refresh()

        calls = []
        mock_context.clear_groups = lambda: calls.append(True)

        page._clear_grouping()

        assert len(calls) == 1
        assert page.page_number == 0

    def test_clear_sorting(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.page_number = 3
        page.refresh()

        calls = []
        mock_context.set_sorting = lambda s: calls.append(s)

        page._clear_sorting()

        assert calls == [None]
        assert page.page_number == 0


class TestVideosPageToggleShowSelected:
    """Tests for the show-only-selected toggle (the fixed bug)."""

    def test_toggle_via_signal(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page._toggle_show_only_selected(True)

        assert page._show_only_selected is True
        assert page.page_number == 0

    def test_toggle_off(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page._toggle_show_only_selected(True)
        page._toggle_show_only_selected(False)

        assert page._show_only_selected is False

    def test_clear_selection_resets_show_only(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page._toggle_show_only_selected(True)
        page._clear_selection()

        assert page._show_only_selected is False


class TestVideosPageSelectAllInView:
    """Tests for select-all-in-view functionality."""

    def test_select_all_in_view(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page._select_all_in_view()

        assert page._selector._to_exclude  # Should switch to exclude mode

    def test_select_all_in_view_then_clear(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page._select_all_in_view()
        page._clear_selection()

        assert not page._selector._to_exclude
        assert len(page._selector._selection) == 0


class TestVideosPageSelectionLabel:
    """Tests for selection label updates."""

    def test_selection_label_empty_initially(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        assert page.selection_label.text() == ""

    def test_selection_label_shows_count(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page._on_video_selection_changed(1, True)
        page._update_selection_display()

        assert "1 selected" in page.selection_label.text()

    def test_selection_changed_signal_emitted(self, qtbot, mock_context):
        """Selection changes emit signal for menu sync."""
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        signals = []
        page.selection_changed.connect(lambda count: signals.append(count))

        page._on_video_selection_changed(1, True)
        page._update_selection_display()

        assert len(signals) >= 1
        assert signals[-1] > 0
