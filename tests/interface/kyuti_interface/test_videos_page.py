"""
Tests for PySide6 VideosPage.

Tests the main video browsing page with mock database.
"""

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QFocusEvent
from PySide6.QtWidgets import QApplication, QMessageBox

from pysaurus.interface.kyuti.pages.videos_page import VideosPage


class TestVideosPageCreation:
    """Tests for VideosPage initialization."""

    def test_page_creation(self, qtbot, mock_context):
        """Test that VideosPage can be created."""

        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        assert page.ctx == mock_context
        assert page.page_size == 20
        assert page.page_number == 0

    def test_page_has_search_input(self, qtbot, mock_context):
        """Test that VideosPage has a search input."""

        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        assert page.search_input is not None

    def test_page_has_pagination(self, qtbot, mock_context):
        """Test that VideosPage has pagination controls."""

        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        assert page.btn_prev is not None
        assert page.btn_next is not None
        assert page.page_button is not None


class TestVideosPageRefresh:
    """Tests for VideosPage refresh functionality."""

    def test_refresh_loads_videos(self, qtbot, mock_context):
        """Test that refresh loads videos from database."""

        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        page.refresh()

        # Should have loaded videos
        assert page._videos is not None
        assert len(page._videos) > 0

    def test_refresh_updates_page_count(self, qtbot, mock_context):
        """Test that refresh updates total page count."""

        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        page.refresh()

        # With 5 test videos and page_size=20, should have 1 page
        assert page._total_pages >= 1


class TestVideosPageSelection:
    """Tests for video selection functionality."""

    def test_initial_selector_is_empty(self, qtbot, mock_context):
        """Test that initial selector has no selections."""

        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        # Selector should be in include mode with empty selection
        assert not page._selector._to_exclude
        assert len(page._selector._selection) == 0

    def test_select_all_in_page(self, qtbot, mock_context):
        """Test selecting all videos in current page."""

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Select all in page
        page._select_all()

        # Should have selections
        assert len(page._selector._selection) > 0

    def test_clear_selection(self, qtbot, mock_context):
        """Test clearing selection."""

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

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        video_id = 1
        # Simulate selection change via the handler
        page._on_video_selection_changed(video_id, True)

        assert video_id in page._selector._selection

    def test_selection_buttons_visibility(self, qtbot, mock_context):
        """Hide "Page" on a single page; hide both when the view is empty."""
        page = VideosPage(mock_context)
        qtbot.addWidget(page)

        # Multiple pages (page_size 1, 4 videos in view): both buttons shown.
        page.page_size = 1
        page.refresh()
        assert not page.btn_select_page.isHidden()
        assert not page.btn_select_all.isHidden()

        # Single page (all videos fit): "Page" hidden, "All" still shown.
        page.page_size = 20
        page.page_number = 0
        page.refresh()
        assert page.btn_select_page.isHidden()
        assert not page.btn_select_all.isHidden()

        # Empty view: both hidden.
        mock_context.set_search("zzz_nonexistent_query_xyz", "and")
        page.refresh()
        assert page.btn_select_page.isHidden()
        assert page.btn_select_all.isHidden()


class TestVideosPagePagination:
    """Tests for pagination functionality."""

    def test_next_page(self, qtbot, mock_context):
        """Test going to next page."""

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

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.page_size = 2
        page.page_number = 1  # Start on second page
        page.refresh()

        page._go_prev()
        assert page.page_number == 0

    def test_prev_page_at_start(self, qtbot, mock_context):
        """Test that prev page does nothing at start."""

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

    def test_property_value_click_calls_focus_prop_val(self, qtbot, mock_context):
        """Test that property value click calls focus_prop_val."""

        # Track calls to focus_prop_val
        calls = []
        original_method = mock_context.focus_prop_val

        def mock_focus(prop_name, value):
            calls.append((prop_name, value))

        mock_context.focus_prop_val = mock_focus

        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Simulate property value click
        page._on_property_value_clicked("genre", "action")

        assert len(calls) == 1
        assert calls[0] == ("genre", "action")

        # Restore original
        mock_context.focus_prop_val = original_method


class TestVideosPageSelector:
    """Tests for the Selector class integration."""

    def test_selector_include_mode(self, qtbot, mock_context):
        """Test selector in include mode (add individual videos)."""

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

    def test_search_button_uses_visible_text_after_focus_loss(
        self, qtbot, mock_context
    ):
        """Typing a new query over an active search, then clicking a mode
        button, must search the VISIBLE text. Clicking a button pulls focus off
        the field first (FocusOut); that must not revert the field to the
        previous search text before the click is handled."""
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page._active_search_text = "abc"  # a previous search is active
        page.search_input.setText("xyz")  # user types a new query

        calls = []
        mock_context.set_search = lambda text, cond: calls.append((text, cond))

        # Reproduce the real event order of a button click while the field has
        # focus: FocusOut is delivered before the button's clicked handler runs.
        QApplication.sendEvent(page.search_input, QFocusEvent(QEvent.Type.FocusOut))
        page._on_search_or()

        assert calls == [("xyz", "or")]

    def test_search_clears_focus_so_shortcuts_work_after(self, qtbot, mock_context):
        """After a search runs, search_input must release focus so a
        following Ctrl+A/Ctrl+Shift+A/... page shortcut reaches the page
        instead of being swallowed by QLineEdit's own standard shortcuts
        (e.g. Ctrl+A = select-all-text-in-field)."""
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.show()
        qtbot.waitExposed(page)
        page.refresh()

        page.search_input.setText("test query")
        page.search_input.setFocus()
        qtbot.waitUntil(lambda: page.search_input.hasFocus())

        page._on_search()

        assert not page.search_input.hasFocus()
        assert page.search_input.text() == "test query"

    def test_empty_search_does_not_clear_focus(self, qtbot, mock_context):
        """An empty search is a no-op (test_empty_search_not_applied) and
        must not steal focus from the field the user is still typing in."""
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.show()
        qtbot.waitExposed(page)
        page.refresh()

        page.search_input.setText("")
        page.search_input.setFocus()
        qtbot.waitUntil(lambda: page.search_input.hasFocus())

        page._on_search()

        assert page.search_input.hasFocus()


class TestVideosPageSidebarFocus:
    """Sidebar labels/section backgrounds don't accept focus by default, so
    clicking them was a no-op that left search_input focused. _create_sidebar
    gives them Qt.ClickFocus so a click anywhere in the sidebar releases
    whatever currently has focus."""

    def test_click_sidebar_label_clears_search_focus(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.show()
        qtbot.waitExposed(page)

        page.search_input.setFocus()
        qtbot.waitUntil(lambda: page.search_input.hasFocus())

        qtbot.mouseClick(page.sources_info, Qt.MouseButton.LeftButton)

        assert not page.search_input.hasFocus()


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

    def test_selection_label_shows_no_selection_initially(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        assert page.selection_label.text() == "no selection"

    def test_selection_label_shows_count(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page._on_video_selection_changed(1, True)
        page._update_selection_display()

        assert "1 selected" in page.selection_label.text()


class TestVideosPageGeneralizeProperty:
    """Generalize a video's property values onto the rest of its group.

    Mock data (tests/mocks/test_data.json): video 1 has genre=[action, comedy]
    (multiple) and rating=[8] (single); videos 2-4 have their own values;
    video 5 has none. The mock's apply_on_view resolves the selector against
    every video, so "all except the source" is videos 2-5.
    """

    def _patch_confirm(self, monkeypatch, answer):
        monkeypatch.setattr(
            "pysaurus.interface.kyuti.pages.videos_page.QMessageBox.question",
            lambda *a, **k: answer,
        )

    def test_multiple_property_merges_without_confirmation(
        self, qtbot, mock_context, mock_database
    ):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page._generalize_property_to_group(1, "genre")

        tags = mock_database.videos_tag_get("genre")
        assert set(tags[2]) == {"drama", "action", "comedy"}  # merged, kept drama
        assert set(tags[5]) == {"action", "comedy"}  # had none
        assert set(tags[1]) == {"action", "comedy"}  # source untouched

    def test_single_property_replaces_when_confirmed(
        self, qtbot, mock_context, mock_database, monkeypatch
    ):
        self._patch_confirm(monkeypatch, QMessageBox.StandardButton.Yes)
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page._generalize_property_to_group(1, "rating")

        ratings = mock_database.videos_tag_get("rating")
        assert ratings[2] == [8] and ratings[3] == [8] and ratings[4] == [8]

    def test_single_property_cancelled_changes_nothing(
        self, qtbot, mock_context, mock_database, monkeypatch
    ):
        self._patch_confirm(monkeypatch, QMessageBox.StandardButton.No)
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page._generalize_property_to_group(1, "rating")

        ratings = mock_database.videos_tag_get("rating")
        assert ratings[2] == [9] and ratings[3] == [7] and ratings[4] == [6]

    def test_all_properties_generalizes_every_set_property(
        self, qtbot, mock_context, mock_database, monkeypatch
    ):
        # "All" includes the single-valued "rating", so it asks for confirmation.
        self._patch_confirm(monkeypatch, QMessageBox.StandardButton.Yes)
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page._generalize_all_properties_to_group(1)

        assert set(mock_database.videos_tag_get("genre")[5]) == {"action", "comedy"}
        assert mock_database.videos_tag_get("rating")[5] == [8]
