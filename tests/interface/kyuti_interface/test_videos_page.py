"""
Tests for PySide6 VideosPage.

Tests the main video browsing page with mock database.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QFocusEvent, QMouseEvent
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from pysaurus.database.database_algorithms import SimilarityCopyReport
from pysaurus.database.database_settings import DatabaseSettings
from pysaurus.interface.kyuti.pages.videos_page import VideosPage
from pysaurus.interface.kyuti.widgets.left_click_menu import LeftClickMenu


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

    def test_refresh_purges_stale_included_ids(self, qtbot, mock_context):
        """Data writes can remove videos from the view without bumping the
        view generation (e.g. dropping the property value the view is
        grouped on); refresh must drop those ids from the selection."""
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        real_id = page._videos[0].video_id
        page._on_video_selection_changed(real_id, True)
        # Simulate a stale id: marked while visible, then removed from the
        # view by a data write. 99999 does not exist in the mock database.
        page._selector.include(99999)
        assert page._selector._selection == {real_id, 99999}

        page.refresh()

        assert page._selector._selection == {real_id}

    def test_refresh_purges_stale_excluded_ids(self, qtbot, mock_context):
        """In exclude mode, a stale excluded id distorts the selection count
        (it keeps being subtracted from a total it no longer belongs to)."""
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        page._select_all_in_view()
        real_id = page._videos[0].video_id
        page._on_video_selection_changed(real_id, False)
        page._selector.exclude(99999)

        page.refresh()

        assert page._selector._selection == {real_id}
        assert page._selector.size_from(page._view_count) == len(page._videos) - 1

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


class TestVideosPageContextMenu:
    """The compacted context menu: similarity actions and title generalization
    are grouped into submenus."""

    def _submenus(self, page, video_id, monkeypatch):
        """Build the context menu and return {submenu title: [item texts]}.

        Everything is read into plain strings while the menu is alive; Qt
        deletes the child submenus once the parent goes out of scope.
        """
        captured = {}
        monkeypatch.setattr(
            LeftClickMenu,
            "exec",
            lambda self, *a, **k: captured.setdefault("menu", self),
        )
        page._on_video_context_menu(video_id, None)
        menu = captured["menu"]
        return {
            a.text(): [sub.text() for sub in a.menu().actions()]
            for a in menu.actions()
            if a.menu() is not None
        }

    def test_similarity_actions_grouped_into_submenu(
        self, qtbot, mock_context, monkeypatch
    ):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        # Video 3 has similarity_id=1 (>=0) -> a "Similarity" submenu (no
        # re-encoded one), holding Dismiss then Reset.
        submenus = self._submenus(page, 3, monkeypatch)
        assert "Similarity" in submenus
        assert "Similarity (re-encoded)" not in submenus
        assert submenus["Similarity"] == ["Dismiss", "Reset"]

    def test_generalize_submenus_when_grouped_by_similarity(
        self, qtbot, mock_context, monkeypatch
    ):
        mock_context.set_groups(
            field="similarity_id",
            is_property=False,
            sorting="count",
            reverse=True,
            allow_singletons=True,
        )
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()
        assert page._grouped_by_similarity

        # Video 3 has an empty meta_title, so only "File title" shows.
        submenus = self._submenus(page, 3, monkeypatch)
        assert "Generalize title" in submenus
        assert "Generalize property" in submenus
        assert submenus["Generalize title"] == ["File title"]

    def test_generalize_title_targets_the_default_property(
        self, qtbot, mock_context, monkeypatch
    ):
        mock_context.set_groups(
            field="similarity_id",
            is_property=False,
            sorting="count",
            reverse=True,
            allow_singletons=True,
        )
        mock_context.set_database_settings(
            DatabaseSettings(generalize_title_property="genre")
        )
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()

        items = [
            t for t in self._submenus(page, 3, monkeypatch)["Generalize title"] if t
        ]
        assert items == ["File title → genre", "Choose property..."]

    def test_generalize_title_with_a_target_skips_the_dialog(
        self, qtbot, mock_context, mock_database, monkeypatch
    ):
        def no_dialog(self):
            raise AssertionError("the property dialog must not open")

        monkeypatch.setattr(QDialog, "exec", no_dialog)
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()
        title = page._get_video_by_id(3).filename.file_title

        page._generalize_title_to_property(3, "file_title", "genre")

        assert title in mock_database.videos_tag_get("genre")[5]


class TestVideosPageCopySimilarityInfos:
    """The "Copy similarity infos to" submenu lists the rest of the group and,
    without a multiple title property, offers to copy everything but the titles.
    """

    def _grouped_page(self, qtbot, mock_context):
        mock_context.set_groups(
            field="similarity_id",
            is_property=False,
            sorting="count",
            reverse=True,
            allow_singletons=True,
        )
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()
        return page

    def _patch_question(self, monkeypatch, answer, asked):
        def question(*args, **kwargs):
            asked.append(args[2])
            return answer

        monkeypatch.setattr(
            "pysaurus.interface.kyuti.pages.videos_page.QMessageBox.question", question
        )

    def test_submenu_lists_the_other_videos_of_the_view(
        self, qtbot, mock_context, monkeypatch
    ):
        page = self._grouped_page(qtbot, mock_context)
        others = [i for i in mock_context.get_all_view_ids() if i != 3]
        assert others

        submenus = TestVideosPageContextMenu._submenus(self, page, 3, monkeypatch)

        assert submenus["Copy similarity infos to"] == [
            str(mock_context.get_video_by_id(i).filename) for i in others
        ]

    def test_without_title_property_declining_copies_nothing(
        self, qtbot, mock_context, monkeypatch
    ):
        page = self._grouped_page(qtbot, mock_context)
        asked = []
        self._patch_question(monkeypatch, QMessageBox.StandardButton.No, asked)

        page._copy_similarity_infos(3, 4, "movie2")

        assert len(asked) == 1
        assert mock_context.copied == []

    def test_without_title_property_accepting_copies_the_rest(
        self, qtbot, mock_context, monkeypatch
    ):
        page = self._grouped_page(qtbot, mock_context)
        self._patch_question(monkeypatch, QMessageBox.StandardButton.Yes, [])

        page._copy_similarity_infos(3, 4, "movie2")

        assert mock_context.copied == [(3, 4, False)]

    def test_single_valued_title_property_is_refused_by_name(
        self, qtbot, mock_context, monkeypatch
    ):
        # "rating" is single-valued in the mock data.
        mock_context.set_database_settings(
            DatabaseSettings(generalize_title_property="rating")
        )
        page = self._grouped_page(qtbot, mock_context)
        asked = []
        self._patch_question(monkeypatch, QMessageBox.StandardButton.No, asked)

        page._copy_similarity_infos(3, 4, "movie2")

        assert len(asked) == 1 and "rating" in asked[0]
        assert mock_context.copied == []

    def test_multiple_title_property_copies_without_asking(
        self, qtbot, mock_context, monkeypatch
    ):
        # "genre" is a multiple string property in the mock data.
        mock_context.set_database_settings(
            DatabaseSettings(generalize_title_property="genre")
        )
        page = self._grouped_page(qtbot, mock_context)
        self._patch_question(monkeypatch, QMessageBox.StandardButton.No, [])
        messages = []
        page.status_message_requested.connect(lambda m, t: messages.append(m))

        page._copy_similarity_infos(3, 4, "movie2")

        assert mock_context.copied == [(3, 4, True)]
        assert messages == ["Copied to movie2: 1 property(ies), watched"]

    def test_summary_reports_kept_values_and_nothing_new(self):
        summary = VideosPage._copy_summary
        report = SimilarityCopyReport(kept=["u"])
        assert summary(report) == "nothing new. Kept destination values for: u"
        report = SimilarityCopyReport(titles=["a", "b"], date_added=True)
        assert summary(report) == "2 title(s), date added"


class TestVideosPageReplaceWith:
    """ "Replace with" copies onto a partner, then removes the original the way
    the dialog said; unique values the destination kept get a last question."""

    def _page(self, qtbot, mock_context, title_property="genre"):
        if title_property:
            mock_context.set_database_settings(
                DatabaseSettings(generalize_title_property=title_property)
            )
        mock_context.set_groups(
            field="similarity_id",
            is_property=False,
            sorting="count",
            reverse=True,
            allow_singletons=True,
        )
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()
        return page

    def _patch_dialog(self, monkeypatch, mode, asked=None):
        def ask(video, dst_title, note=None, parent=None):
            if asked is not None:
                asked.append((video.video_id, dst_title, note))
            return mode

        monkeypatch.setattr(
            "pysaurus.interface.kyuti.pages.videos_page.ReplaceVideoDialog.ask", ask
        )

    def _patch_question(self, monkeypatch, answer):
        monkeypatch.setattr(
            "pysaurus.interface.kyuti.pages.videos_page.QMessageBox.question",
            lambda *a, **k: answer,
        )

    def _record_removals(self, monkeypatch, mock_context):
        removed = []
        for name, mode in (
            ("trash_video", "trash"),
            ("delete_video_file", "delete"),
            ("delete_video_entry", "entry"),
        ):
            monkeypatch.setattr(
                mock_context, name, lambda vid, m=mode: removed.append((m, vid))
            )
        return removed

    def test_submenu_lists_the_partners(self, qtbot, mock_context, monkeypatch):
        page = self._page(qtbot, mock_context)
        submenus = TestVideosPageContextMenu._submenus(self, page, 3, monkeypatch)
        assert submenus["Replace with"] == submenus["Copy similarity infos to"]

    @pytest.mark.parametrize(
        "mode,removed_word",
        [
            ("trash", "moved to trash"),
            ("delete", "permanently deleted"),
            ("entry", "removed from database"),
        ],
    )
    def test_copies_then_removes_as_the_dialog_said(
        self, qtbot, mock_context, monkeypatch, mode, removed_word
    ):
        page = self._page(qtbot, mock_context)
        self._patch_dialog(monkeypatch, mode)
        removed = self._record_removals(monkeypatch, mock_context)
        messages = []
        page.status_message_requested.connect(lambda m, t: messages.append(m))

        page._replace_video(3, 4, "movie2")

        assert mock_context.copied == [(3, 4, True)]
        assert removed == [(mode, 3)]
        assert messages == [
            f"'movie1' replaced with 'movie2' and {removed_word}: "
            "1 property(ies), watched"
        ]

    def test_cancelling_the_dialog_does_nothing(self, qtbot, mock_context, monkeypatch):
        page = self._page(qtbot, mock_context)
        self._patch_dialog(monkeypatch, None)
        removed = self._record_removals(monkeypatch, mock_context)

        page._replace_video(3, 4, "movie2")

        assert mock_context.copied == []
        assert removed == []

    def test_without_title_property_the_dialog_carries_the_note(
        self, qtbot, mock_context, monkeypatch
    ):
        page = self._page(qtbot, mock_context, title_property=None)
        asked = []
        self._patch_dialog(monkeypatch, "trash", asked)
        removed = self._record_removals(monkeypatch, mock_context)

        page._replace_video(3, 4, "movie2")

        assert asked == [(3, "movie2", asked[0][2])] and asked[0][2]
        assert mock_context.copied == [(3, 4, False)]
        assert removed == [("trash", 3)]

    def test_kept_values_refused_keeps_the_original(
        self, qtbot, mock_context, monkeypatch
    ):
        page = self._page(qtbot, mock_context)
        mock_context.copy_report = SimilarityCopyReport(kept=["rating"])
        self._patch_dialog(monkeypatch, "trash")
        self._patch_question(monkeypatch, QMessageBox.StandardButton.No)
        removed = self._record_removals(monkeypatch, mock_context)
        messages = []
        page.status_message_requested.connect(lambda m, t: messages.append(m))

        page._replace_video(3, 4, "movie2")

        assert mock_context.copied == [(3, 4, True)]
        assert removed == []
        assert messages == [
            "Copied to movie2: nothing new. Kept destination values for: rating"
        ]

    def test_kept_values_accepted_removes_the_original(
        self, qtbot, mock_context, monkeypatch
    ):
        page = self._page(qtbot, mock_context)
        mock_context.copy_report = SimilarityCopyReport(kept=["rating"])
        self._patch_dialog(monkeypatch, "delete")
        self._patch_question(monkeypatch, QMessageBox.StandardButton.Yes)
        removed = self._record_removals(monkeypatch, mock_context)

        page._replace_video(3, 4, "movie2")

        assert removed == [("delete", 3)]

    def test_failed_removal_keeps_the_copy_and_warns(
        self, qtbot, mock_context, monkeypatch
    ):
        page = self._page(qtbot, mock_context)
        self._patch_dialog(monkeypatch, "trash")

        def failing(vid):
            raise OSError("locked")

        monkeypatch.setattr(mock_context, "trash_video", failing)
        warnings = []
        monkeypatch.setattr(
            "pysaurus.interface.kyuti.pages.videos_page.QMessageBox.warning",
            lambda *a, **k: warnings.append(a[2]),
        )
        messages = []
        page.status_message_requested.connect(lambda m, t: messages.append(m))

        page._replace_video(3, 4, "movie2")

        assert mock_context.copied == [(3, 4, True)]
        assert len(warnings) == 1 and "locked" in warnings[0]
        assert messages == []


class TestVideosPageFileDrag:
    """Dragging videos out of the list into an external program."""

    def _page(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.refresh()
        return page

    def _dropped(self, mime_data):
        return [Path(url.toLocalFile()) for url in mime_data.urls()]

    def _mouse(self, event_type, pos, buttons):
        return QMouseEvent(
            event_type,
            pos,
            pos,
            Qt.MouseButton.LeftButton,
            buttons,
            Qt.KeyboardModifier.NoModifier,
        )

    def test_unselected_video_drags_only_itself(self, qtbot, mock_context):
        page = self._page(qtbot, mock_context)
        video = page._videos[0]

        mime_data = page._build_drag_mime_data(video.video_id)

        assert self._dropped(mime_data) == [Path(video.filename.standard_path)]

    def test_selected_video_drags_the_whole_selection(self, qtbot, mock_context):
        page = self._page(qtbot, mock_context)
        first, second = page._videos[0], page._videos[1]
        page._selector.include(first.video_id)
        page._selector.include(second.video_id)

        mime_data = page._build_drag_mime_data(first.video_id)

        assert sorted(self._dropped(mime_data)) == sorted(
            [Path(first.filename.standard_path), Path(second.filename.standard_path)]
        )

    def test_unselected_video_ignores_the_selection(self, qtbot, mock_context):
        """Dragging outside the selection must not carry it along, the way a
        file manager drags only the item under the cursor."""
        page = self._page(qtbot, mock_context)
        first, second = page._videos[0], page._videos[1]
        page._selector.include(second.video_id)

        mime_data = page._build_drag_mime_data(first.video_id)

        assert self._dropped(mime_data) == [Path(first.filename.standard_path)]

    def test_select_all_drags_the_whole_view(self, qtbot, mock_context):
        """ "Select all" is view-wide, not page-wide: the drag resolves it
        backend-side instead of reading the current page."""
        page = self._page(qtbot, mock_context)
        page._select_all_in_view()

        mime_data = page._build_drag_mime_data(page._videos[0].video_id)

        dropped = self._dropped(mime_data)
        assert len(dropped) >= len(page._videos)
        for video in page._videos:
            assert Path(video.filename.standard_path) in dropped

    def test_no_database_drags_nothing(self, qtbot, mock_context):
        page = self._page(qtbot, mock_context)
        video_id = page._videos[0].video_id
        mock_context._database = None

        assert page._build_drag_mime_data(video_id) is None

    def test_left_drag_on_the_list_starts_a_file_drag(self, qtbot, mock_context):
        """VideoListItem ignores mouse presses, so they propagate to the
        viewport: that is where the gesture must be picked up."""
        page = self._page(qtbot, mock_context)
        started = []
        page._start_file_drag = started.append
        viewport = page.list_widget.viewport()
        origin = QPointF(30, 30)
        far = QPointF(30 + QApplication.startDragDistance() + 10, 30)

        QApplication.sendEvent(
            viewport,
            self._mouse(
                QEvent.Type.MouseButtonPress, origin, Qt.MouseButton.LeftButton
            ),
        )
        QApplication.sendEvent(
            viewport, self._mouse(QEvent.Type.MouseMove, far, Qt.MouseButton.LeftButton)
        )

        assert started == [origin.toPoint()]

    def test_small_move_starts_no_drag(self, qtbot, mock_context):
        """Below the drag threshold the gesture is still a click, not a drag."""
        page = self._page(qtbot, mock_context)
        started = []
        page._start_file_drag = started.append
        viewport = page.list_widget.viewport()

        QApplication.sendEvent(
            viewport,
            self._mouse(
                QEvent.Type.MouseButtonPress, QPointF(30, 30), Qt.MouseButton.LeftButton
            ),
        )
        QApplication.sendEvent(
            viewport,
            self._mouse(
                QEvent.Type.MouseMove, QPointF(31, 31), Qt.MouseButton.LeftButton
            ),
        )

        assert started == []

    def test_move_after_release_starts_no_drag(self, qtbot, mock_context):
        """Hovering the list with no button held must never start a drag."""
        page = self._page(qtbot, mock_context)
        started = []
        page._start_file_drag = started.append
        viewport = page.list_widget.viewport()
        far = QPointF(30 + QApplication.startDragDistance() + 10, 30)

        QApplication.sendEvent(
            viewport,
            self._mouse(
                QEvent.Type.MouseButtonPress, QPointF(30, 30), Qt.MouseButton.LeftButton
            ),
        )
        QApplication.sendEvent(
            viewport,
            self._mouse(
                QEvent.Type.MouseButtonRelease, QPointF(30, 30), Qt.MouseButton.NoButton
            ),
        )
        QApplication.sendEvent(
            viewport, self._mouse(QEvent.Type.MouseMove, far, Qt.MouseButton.NoButton)
        )

        assert started == []

    def test_drag_hint_follows_the_selection(self, qtbot, mock_context):
        """The gesture has no affordance of its own, so the hint is the only
        thing announcing it: it must show exactly while a selection exists."""
        page = self._page(qtbot, mock_context)
        assert page.drag_hint_label.isHidden()

        page._select_all()

        assert not page.drag_hint_label.isHidden()

        page._clear_selection()

        assert page.drag_hint_label.isHidden()


class TestVideosPageSelectionMenu:
    """The selection menu acts on the whole selection, every page included."""

    def _page(self, qtbot, mock_context):
        page = VideosPage(mock_context)
        qtbot.addWidget(page)
        page.page_size = 1
        page.refresh()
        assert len(page._videos) == 1
        return page

    def _menu(self, page, monkeypatch):
        captured = {}
        monkeypatch.setattr(
            LeftClickMenu,
            "exec",
            lambda self, *a, **k: captured.setdefault("menu", self),
        )
        page._on_selection_menu()
        return captured["menu"]

    @staticmethod
    def _messages(page):
        messages = []
        page.status_message_requested.connect(lambda text, _ms: messages.append(text))
        return messages

    @staticmethod
    def _watched(mock_database):
        return {v["video_id"]: v["watched"] for v in mock_database._videos}

    @staticmethod
    def _genre(mock_database, video_id=1):
        video = next(v for v in mock_database._videos if v["video_id"] == video_id)
        return video["properties"]["genre"]

    def _patch_dialog(self, monkeypatch, mode, asked):
        def ask(nb_videos, in_path, in_title, parent=None):
            asked.append((nb_videos, in_path, in_title))
            return {"path": in_path, "title": in_title, None: None}[mode]

        monkeypatch.setattr(
            "pysaurus.interface.kyuti.pages.videos_page.BatchRedundantValuesDialog.ask",
            ask,
        )

    def test_menu_groups_watched_actions_and_offers_the_cleanup(
        self, qtbot, mock_context, monkeypatch
    ):
        page = self._page(qtbot, mock_context)
        page._select_all_in_view()
        menu = self._menu(page, monkeypatch)
        actions = [a for a in menu.actions() if not a.isSeparator()]
        assert [a.text() for a in actions] == [
            "Show Only Selected\tCtrl+Shift+D",
            "Set Watched",
            "Edit Properties",
            "Remove redundant values...",
        ]
        assert [a.text() for a in actions[1].menu().actions()] == [
            "Toggle",
            "Mark as Watched",
            "Mark as Unwatched",
        ]
        assert all(a.isEnabled() for a in actions[1:])

    def test_menu_actions_are_disabled_without_selection(
        self, qtbot, mock_context, monkeypatch
    ):
        page = self._page(qtbot, mock_context)
        menu = self._menu(page, monkeypatch)
        by_text = {a.text(): a for a in menu.actions()}
        assert not by_text["Set Watched"].isEnabled()
        assert not by_text["Edit Properties"].isEnabled()
        assert not by_text["Remove redundant values..."].isEnabled()

    def test_mark_as_watched_reaches_selected_videos_beyond_the_page(
        self, qtbot, mock_context, mock_database
    ):
        page = self._page(qtbot, mock_context)
        page._selector.include(1)
        page._selector.include(3)
        messages = self._messages(page)

        page._set_watched_selection(True)

        watched = self._watched(mock_database)
        assert watched[1] and watched[3] and not watched[5]
        assert messages == ["2 video(s) marked as watched"]

    def test_mark_as_unwatched_counts_only_changes(
        self, qtbot, mock_context, mock_database
    ):
        page = self._page(qtbot, mock_context)
        page._select_all_in_view()
        messages = self._messages(page)

        page._set_watched_selection(False)

        assert not any(self._watched(mock_database).values())
        assert messages == ["2 video(s) marked as unwatched"]

    def test_toggle_flips_the_whole_selection(self, qtbot, mock_context, mock_database):
        page = self._page(qtbot, mock_context)
        before = self._watched(mock_database)
        page._select_all_in_view()
        messages = self._messages(page)

        page._on_toggle_watched_selection()

        assert self._watched(mock_database) == {v: not w for v, w in before.items()}
        assert messages == ["Watched status toggled for 5 video(s)"]

    def test_without_selection_nothing_happens(
        self, qtbot, mock_context, mock_database, monkeypatch
    ):
        page = self._page(qtbot, mock_context)
        before = self._watched(mock_database)
        messages = self._messages(page)
        asked = []
        self._patch_dialog(monkeypatch, "path", asked)

        page._set_watched_selection(True)
        page._on_toggle_watched_selection()
        page._remove_redundant_values_from_selection()

        assert self._watched(mock_database) == before
        assert messages == []
        assert asked == []

    def test_cleanup_removes_what_the_path_mode_found(
        self, qtbot, mock_context, mock_database, monkeypatch
    ):
        # "video1" is the file title; "videos" is only in the parent folder.
        self._genre(mock_database).extend(["video1", "videos"])
        page = self._page(qtbot, mock_context)
        page._selector.include(1)
        page._selector.include(3)
        asked = []
        self._patch_dialog(monkeypatch, "path", asked)
        messages = self._messages(page)

        page._remove_redundant_values_from_selection()

        assert asked == [
            (2, {1: {"genre": ["video1", "videos"]}}, {1: {"genre": ["video1"]}})
        ]
        assert self._genre(mock_database) == ["action", "comedy"]
        assert messages == ["Removed 2 redundant value(s) from 1 video(s)"]

    def test_cleanup_in_title_mode_spares_folder_words(
        self, qtbot, mock_context, mock_database, monkeypatch
    ):
        self._genre(mock_database).extend(["video1", "videos"])
        page = self._page(qtbot, mock_context)
        page._selector.include(1)
        self._patch_dialog(monkeypatch, "title", [])
        messages = self._messages(page)

        page._remove_redundant_values_from_selection()

        assert self._genre(mock_database) == ["action", "comedy", "videos"]
        assert messages == ["Removed 1 redundant value(s) from 1 video(s)"]

    def test_cancelling_the_cleanup_keeps_everything(
        self, qtbot, mock_context, mock_database, monkeypatch
    ):
        self._genre(mock_database).extend(["video1", "videos"])
        page = self._page(qtbot, mock_context)
        page._selector.include(1)
        self._patch_dialog(monkeypatch, None, [])
        messages = self._messages(page)

        page._remove_redundant_values_from_selection()

        assert self._genre(mock_database) == ["action", "comedy", "video1", "videos"]
        assert messages == []

    def test_cleanup_informs_when_nothing_is_found(
        self, qtbot, mock_context, monkeypatch
    ):
        page = self._page(qtbot, mock_context)
        page._selector.include(1)
        page._selector.include(3)
        asked = []
        self._patch_dialog(monkeypatch, "path", asked)
        infos = []
        monkeypatch.setattr(
            "pysaurus.interface.kyuti.pages.videos_page.QMessageBox.information",
            lambda parent, title, text: infos.append((title, text)),
        )
        messages = self._messages(page)

        page._remove_redundant_values_from_selection()

        assert infos == [("Remove redundant values", "No redundant value found.")]
        assert asked == []
        assert messages == []
