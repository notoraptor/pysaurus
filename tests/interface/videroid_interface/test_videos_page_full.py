"""Full coverage for the Videos page: filters, groups/classifier, selection,
batch + per-video actions, pagination. Backend-constrained or external calls
(classifier, open/trash/delete files, clipboard) are mocked."""

from unittest.mock import Mock

import pytest

from pysaurus.core.constants import VIDEO_DEFAULT_SORTING
from pysaurus.interface.common.common import FIELD_MAP
from pysaurus.interface.videroid.dialogs.batch_edit_property_dialog import (
    BatchEditPropertyDialog,
)
from pysaurus.interface.videroid.dialogs.grouping_dialog import GroupingDialog
from pysaurus.interface.videroid.dialogs.sorting_dialog import SortingDialog
from pysaurus.interface.videroid.dialogs.sources_dialog import SourcesDialog


def _evt(**attrs):
    return type("Evt", (), attrs)()


@pytest.fixture
def vp(videroid_app):
    app, window = videroid_app
    app.show_page("videos")
    window.render()
    return app, window, app._pages["videos"]


def _video(app):
    return app.context.get_videos(1, 0).result[0]


def _setup_multiple_prop(app, page, name="tag", values=("x",)):
    """Create a multiple str property, tag the first video with `values`, group
    by it, reload. Lets tests drive the real classifier (no mocks)."""
    ctx = app.context
    db = ctx._api.database
    ctx.create_prop_type(name, "str", "", True)
    vid = _video(app).video_id
    with db.to_save():
        db.videos_tag_set(name, {vid: list(values)})
    ctx.set_groups(name, is_property=True)
    page._reload()


def _stack_group(page, value):
    """Select the group whose value == `value` and push it onto the classifier."""
    stats = page._context.classifier_stats or []
    idx = next(i for i, s in enumerate(stats) if str(s.value) == value)
    page._select_group(idx)
    page._on_add_classifier(None)


def _group_by_tag_two_videos(app, name="tag"):
    """Tag two distinct videos with distinct values and group by that property,
    guaranteeing >= 2 groups (so group navigation/listing is meaningful)."""
    ctx = app.context
    db = ctx._api.database
    ctx.create_prop_type(name, "str", "", True)
    vids = [v.video_id for v in ctx.get_videos(2, 0).result]
    with db.to_save():
        db.videos_tag_set(name, {vids[0]: ["a"], vids[1]: ["b"]})
    ctx.set_groups(name, is_property=True)


class TestFilters:
    def test_search_applies_and_clears(self, vp):
        _, _, page = vp
        page._search_input.value = "foo"
        page._on_mode(_evt(data="and"))  # set_search("foo", "and")
        assert "foo" in page._search_status.text  # search really registered
        page._clear_search(None)
        assert page._search_input.value == ""
        assert "no search" in page._search_status.text.lower()

    def test_sorting_apply_changes_order_then_clears(self, vp):
        _, _, page = vp
        page._open_sorting(None)  # opens the fancybox (UI smoke)
        # Apply a sort that DIFFERS from the default (-date), and check it took.
        field = next(f for f in FIELD_MAP.sortable if f.name != "date")
        page._apply_sorting(_evt(data=SortingDialog([f"-{field.name}"])))
        assert field.title in page._sorting_display.text
        assert "▼" in page._sorting_display.text  # reverse arrow
        page._clear_sorting(None)  # back to VIDEO_DEFAULT_SORTING (-date)
        default_field = FIELD_MAP.fields[VIDEO_DEFAULT_SORTING[0].lstrip("+-")]
        assert default_field.title in page._sorting_display.text

    def test_sources_simple_then_advanced_expression(self, vp):
        app, _, page = vp
        page._open_sources(None)
        page._apply_sources(_evt(data=SourcesDialog()))  # default -> "valid" source
        assert page._sources_display.text != "(none)"
        # Clear here (before any expression) so the "All readable" default shows.
        page._clear_sources(None)  # set_sources([]) -> default [["readable"]]
        assert page._sources_display.text == "All readable"
        # Now the Advanced tab: a free-text expression.
        advanced = SourcesDialog(current_expression="width > 0")
        advanced._tabs._on_click(_evt(data=1))  # switch to the Advanced tab
        assert advanced.is_advanced()
        page._apply_sources(_evt(data=advanced))  # -> set_source_expression
        assert app.context.get_source_expression() == "width > 0"
        assert "expr: width > 0" in page._sources_display.text

    def test_grouping_apply_then_clear(self, vp):
        app, _, page = vp
        page._open_grouping(None)
        names = [p.name for p in app.context.get_prop_types()]
        dialog = GroupingDialog(names)
        result = dialog.get_result()  # first attribute field, is_property=False
        page._apply_grouping(_evt(data=dialog))
        grouped = app.context.get_videos(page.page_size, 0)
        assert grouped.grouping is not None
        assert grouped.grouping.field == result["field"]
        assert page._sec_groups in page._sidebar_column.controls  # Groups section shown
        page._clear_grouping(None)
        cleared = app.context.get_videos(page.page_size, 0)
        assert cleared.grouping is None or cleared.grouping.field is None
        assert page._sec_groups not in page._sidebar_column.controls


class TestGroupsClassifier:
    def test_group_navigation_moves_selected_group(self, vp):
        app, _, page = vp
        _group_by_tag_two_videos(app)  # guarantees >= 2 groups
        page._reload()
        ngroups = len(page._context.classifier_stats)
        assert ngroups >= 2  # need several groups for navigation to be meaningful
        page._group_last(None)
        assert page._context.group_id == ngroups - 1
        page._group_first(None)
        assert page._context.group_id == 0
        page._group_next(None)
        assert page._context.group_id == 1
        page._group_prev(None)
        assert page._context.group_id == 0
        page._on_group_click(_evt(data=1))  # click selects that group
        assert page._context.group_id == 1

    def test_populate_classifier_badges(self, vp):
        _, _, page = vp
        ctx = Mock()
        ctx.classifier = ["a", "b"]
        page._populate_classifier(ctx)
        assert len(page._classifier_column.controls) == 2  # one badge per path level

    def test_populate_groups_lists_every_group(self, vp):
        app, _, page = vp
        _group_by_tag_two_videos(app)
        ctx = app.context.get_videos(page.page_size, 0)
        page._populate_groups(ctx)
        nstats = len(ctx.classifier_stats)
        assert nstats >= 2
        assert len(page._groups_column.controls) == nstats  # one row per group
        assert page._group_nav_label.text == f"1 / {nstats}"
        page._update_grouping(ctx)
        assert "tag" in page._grouping_display.text

    def test_classifier_real_flow_stacks_value(self, vp):
        app, _, page = vp
        _setup_multiple_prop(app, page)
        _stack_group(page, "x")  # select the "x" group, add to classifier
        assert list(page.context.get_videos(page.page_size, 0).classifier) == ["x"]
        assert len(page._classifier_column.controls) == 1  # one badge for "x"

    def test_classifier_reverse_and_unstack(self, vp):
        app, _, page = vp
        _setup_multiple_prop(app, page, values=("x", "y"))
        _stack_group(page, "x")  # classifier = ["x"]
        _stack_group(page, "y")  # drill down: classifier = ["x", "y"]
        assert list(page._context.classifier) == ["x", "y"]
        page._classifier_reverse(None)
        assert list(page._context.classifier) == ["y", "x"]  # order really reversed
        page._classifier_unstack(None)
        assert list(page._context.classifier) == ["y"]  # last level popped


class TestSelection:
    def test_card_check_and_counter(self, vp):
        app, _, page = vp
        vid = _video(app).video_id
        page._on_card_check(_evt(checked=True, data=vid))
        assert "1 selected" in page._selection_label.text
        page._on_card_check(_evt(checked=False, data=vid))
        assert "no selection" in page._selection_label.text

    def test_selection_menu_and_show_only(self, vp):
        _, _, page = vp
        page._select_all_in_view(None)
        page._refresh_selection_menu()
        assert page._selection_menu.actions  # menu populated with selection actions
        page._toggle_show_only_selected()
        assert page._show_only_selected is True  # toggled on
        page._toggle_show_only_selected()
        assert page._show_only_selected is False  # toggled back off

    def test_selection_toggle_watched_flips_then_restores(self, vp):
        app, _, page = vp

        def watched():
            return {
                v.video_id: v.watched for v in app.context.get_videos(1000, 0).result
            }

        before = watched()
        page._select_all_in_view(None)
        page._selection_toggle_watched()
        once = watched()
        assert once != before  # toggling the selection really changed watched flags
        page._select_all_in_view(None)
        page._selection_toggle_watched()
        assert watched() == before  # double toggle is the identity (involution)

    def test_delete_selected_flow(self, vp):
        app, _, page = vp
        before = app.context.get_videos(1000, 0).view_count
        page.page_size = 1
        page._reset_and_reload()
        page._select_page(None)  # select the single video on the current page
        ids = page._selected_ids()
        assert len(ids) == 1
        page._delete_selected()  # confirm fancybox
        page._do_delete_selected(ids)  # real backend delete (entries only)
        after = app.context.get_videos(1000, 0).view_count
        assert after == before - len(ids)

    def test_delete_selected_no_selection_is_noop(self, vp):
        _, _, page = vp
        page._clear_selection()
        page._delete_selected()  # no ids -> early return, no fancybox
        assert page.app.window.has_fancybox() is False

    def test_clear_selection_while_show_only(self, vp):
        _, _, page = vp
        page._select_all_in_view(None)
        page._show_only_selected = True
        page._clear_selection()  # was_show_only -> reset+reload path
        assert page._show_only_selected is False

    def test_toggle_show_only_without_selection_is_noop(self, vp):
        _, _, page = vp
        page._clear_selection()
        page._toggle_show_only_selected()  # nothing selected -> early return
        assert page._show_only_selected is False

    def test_refresh_selection_menu_without_menu(self, vp):
        _, _, page = vp
        page._selection_menu = None
        page._refresh_selection_menu()  # guard: no menu yet -> early return

    def test_edit_property_for_selection_writes_value(self, vp):
        app, _, page = vp
        app.context.create_prop_type("mood", "str", "", True)  # multiple, no enum
        prop = next(p for p in app.context.get_prop_types() if p.name == "mood")
        page._select_all_in_view(None)
        page._edit_property_for_selection(prop)  # opens the batch dialog (UI)
        # Empty changes -> apply is a no-op (no write, no crash).
        page._apply_batch_edit(
            "mood",
            page._selector.to_dict(),
            Mock(**{"get_changes.return_value": ([], [])}),
        )
        # Now stage a real value and apply it to the whole selection.
        dialog = BatchEditPropertyDialog(prop, page._view_count, [])
        dialog._editor.value = "calm"
        dialog._on_add_new(None)  # promote "calm" into 'To add'
        assert dialog.get_changes() == (["calm"], [])
        page._apply_batch_edit("mood", page._selector.to_dict(), dialog)
        vids = app.context.get_videos(1000, 0).result
        assert vids and all("calm" in (v.properties.get("mood") or []) for v in vids)


class TestVideoActions:
    def test_open_and_folder_and_copy(self, vp, monkeypatch):
        app, _, page = vp
        video = _video(app)
        opened, foldered, copied = [], [], []
        monkeypatch.setattr(page.context, "open_video", opened.append)
        monkeypatch.setattr(page.context, "open_containing_folder", foldered.append)
        monkeypatch.setattr("pyperclip.copy", copied.append)
        page.video_open(video)
        page.video_open_folder(video)
        page.video_copy(video, "title")
        assert opened == [video.video_id]  # right id forwarded to the player
        assert foldered == [video.video_id]
        assert copied == [str(video.title)]  # the chosen field is copied verbatim

    def test_rename(self, vp, monkeypatch):
        app, _, page = vp
        video = _video(app)
        renamed = []
        # rename_video does a real os.rename on disk -> mock it.
        monkeypatch.setattr(
            page.context, "rename_video", lambda i, t: renamed.append((i, t))
        )
        page.video_rename(video)  # fancybox
        page._do_rename(video, type("E", (), {"value": "renamed_title"})())
        assert renamed == [(video.video_id, "renamed_title")]

    def test_delete_trash_deletefile(self, vp, monkeypatch):
        app, window, page = vp
        video = _video(app)
        monkeypatch.setattr(page.context, "trash_video", lambda i: None)
        monkeypatch.setattr(page.context, "delete_video_file", lambda i: None)
        # Each action opens a confirm fancybox; clear it before the next (the
        # window asserts a single fancybox at a time, mirroring a real close).
        page.video_delete_entry(video)
        window.clear_fancybox()
        page.video_trash(video)
        window.clear_fancybox()
        page.video_delete_file(video)
        window.clear_fancybox()
        called = []
        page._run_video_action(lambda i: called.append(i), video)
        assert called == [video.video_id]

    def test_toggle_watched(self, vp, monkeypatch):
        app, _, page = vp
        video = _video(app)
        toggled = []
        monkeypatch.setattr(page.context, "toggle_watched", lambda i: toggled.append(i))
        page.video_toggle_watched(video)  # direct action + reload (not _run_*)
        assert toggled == [video.video_id]

    def test_delete_entry_not_found_no_confirm(self, vp, monkeypatch):
        _, _, page = vp
        deleted = []
        monkeypatch.setattr(
            page.context, "delete_video_entry", lambda i: deleted.append(i)
        )
        page.confirm_not_found_deletion = False
        fake = type("V", (), {"found": False, "filename": "gone.mp4", "video_id": 99})()
        page.video_delete_entry(fake)  # not found + no-confirm -> direct delete
        assert deleted == [99]


class TestPagination:
    def test_navigation_moves_between_pages(self, vp):
        _, _, page = vp
        page.page_size = 1  # one video per page -> as many pages as videos
        page._reset_and_reload()
        nb = page._context.nb_pages
        assert nb > 1  # need several pages for navigation to mean anything
        page._last(None)
        assert page._page_number == nb - 1
        assert page._page_label.text == f"Page {nb} / {nb}"
        page._first(None)
        assert page._page_number == 0
        page._next(None)
        assert page._page_number == 1
        page._prev(None)
        assert page._page_number == 0
        page._goto(nb + 5)  # clamps to the last page
        assert page._page_number == nb - 1
        page._goto(-3)  # clamps to the first page
        assert page._page_number == 0


class TestReloadAndFormatting:
    def test_refresh(self, vp):
        _, _, page = vp
        page._status.text = ""
        page.refresh()  # View > Refresh -> reload
        assert "videos" in page._status.text

    def test_reload_without_database(self, vp):
        app, _, page = vp
        app.context._api.database = None  # get_videos -> None
        page._reload()
        assert page._cards.controls[0].text == "No database open."
        assert page._page_label.text == ""

    def test_grouping_display_count_and_length(self, vp):
        _, _, page = vp

        def ctx(sorting):
            grouping = type(
                "G",
                (),
                {
                    "field": "category",
                    "is_property": True,
                    "reverse": False,
                    "sorting": sorting,
                    "allow_singletons": False,
                },
            )()
            return type("C", (), {"grouping": grouping})()

        page._update_grouping(ctx("count"))
        assert page._grouping_display.text.startswith("# ")
        page._update_grouping(ctx("length"))
        assert page._grouping_display.text.startswith("|| ")
