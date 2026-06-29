"""Videos page — video cards + filters sidebar.

Covers display + pagination, the filters sidebar (Sources, Search, Sorting,
Grouping, Groups panel, classifier), multi-selection, and per-video / batch
actions.
"""

from __future__ import annotations

import pyperclip
import videre
from videre.widgets.widget import Widget

from pysaurus.core.classes import Selector
from pysaurus.core.constants import (
    VIDEO_DEFAULT_PAGE_NUMBER,
    VIDEO_DEFAULT_PAGE_SIZE,
    VIDEO_DEFAULT_SORTING,
)
from pysaurus.interface.common.common import FIELD_MAP, format_group_value
from pysaurus.interface.videroid import theme
from pysaurus.interface.videroid.dialogs.batch_edit_property_dialog import (
    BatchEditPropertyDialog,
)
from pysaurus.interface.videroid.dialogs.grouping_dialog import GroupingDialog
from pysaurus.interface.videroid.dialogs.sorting_dialog import SortingDialog
from pysaurus.interface.videroid.dialogs.sources_dialog import SourcesDialog
from pysaurus.interface.videroid.pages.base_page import Page
from pysaurus.interface.videroid.widgets.video_card import VideoCard


class VideosPage(Page):
    title = "Videos"

    def __init__(self, app):
        super().__init__(app)
        self._page_size = VIDEO_DEFAULT_PAGE_SIZE
        self._page_number = VIDEO_DEFAULT_PAGE_NUMBER
        # Options-menu flag, driven by the app shell like page_size. Public to
        # match pyside6 (videos_page.confirm_not_found_deletion). When disabled,
        # deleting a "not found" entry (file gone from disk) skips confirmation.
        self.confirm_not_found_deletion = True
        self._context = None
        # Selection (phase 5b): persists across reloads/pages until cleared.
        self._selector = Selector(False, set())
        self._view_count = 0
        self._show_only_selected = False
        self._selection_label = videre.Text("no selection", italic=True)
        self._selection_menu = None
        # Content widgets.
        self._status = videre.Text("")
        self._cards = videre.Column([], space=0)
        self._page_label = videre.Text("")
        # Sidebar widgets.
        self._sources_display = videre.Text("All readable")
        self._search_input = videre.TextInput()
        self._search_status = videre.Text("(no search)", italic=True)
        self._sorting_display = videre.Text("")
        self._grouping_display = videre.Text("No grouping")
        self._groups_column = videre.Column([], space=2)
        self._group_nav_label = videre.Text("")
        self._add_classifier_holder = videre.Container()
        self._classifier_column = videre.Column([], space=2)
        # Section + sidebar containers (built once in build()).
        self._sidebar_column = videre.Column([], space=8)
        self._sec_sources = None
        self._sec_search = None
        self._sec_sorting = None
        self._sec_grouping = None
        self._sec_groups = None
        self._sec_classifier = None
        self._sec_selection = None

    # --- build --------------------------------------------------------------

    def build(self) -> Widget:
        self._sec_sources = self._sources_section()
        self._sec_search = self._search_section()
        self._sec_sorting = self._sorting_section()
        self._sec_grouping = self._grouping_section()
        self._sec_groups = self._groups_section()
        self._sec_classifier = self._classifier_section()
        self._sec_selection = self._selection_section()
        sidebar = videre.Container(
            videre.ScrollView(self._sidebar_column, wrap_horizontal=True),
            width=240,
            border=videre.Border.all(1, videre.Colors.lightgray),
            padding=videre.Padding.all(6),
        )
        pagination = videre.Row(
            [
                videre.Button("<<", on_click=self._first),
                videre.Button("<", on_click=self._prev),
                self._page_label,
                videre.Button(">", on_click=self._next),
                videre.Button(">>", on_click=self._last),
            ],
            space=5,
            vertical_alignment=videre.Alignment.CENTER,
        )
        content = videre.Column(
            [
                videre.Container(self._status, padding=videre.Padding.all(4)),
                videre.ScrollView(self._cards, wrap_horizontal=True, weight=1),
                videre.Container(
                    pagination,
                    horizontal_alignment=videre.Alignment.CENTER,
                    padding=videre.Padding.all(4),
                ),
            ],
            weight=1,
        )
        widget = videre.Row([sidebar, content], space=6)
        self._reload()
        return widget

    def _section(self, title: str, header_buttons, body) -> Widget:
        return videre.Container(
            videre.Column(
                [
                    videre.Row(
                        [videre.Text(title, strong=True, weight=1), *header_buttons],
                        space=2,
                        vertical_alignment=videre.Alignment.CENTER,
                    ),
                    body,
                ],
                space=4,
            ),
            border=videre.Border.all(1, videre.Colors.lightgray),
            padding=videre.Padding.all(6),
        )

    def _sources_section(self) -> Widget:
        return self._section(
            "Sources",
            [
                videre.Button("⚙", on_click=self._open_sources),
                videre.Button("✕", on_click=self._clear_sources),
            ],
            self._sources_display,
        )

    def _search_section(self) -> Widget:
        return self._section(
            "Search",
            [videre.Button("✕", on_click=self._clear_search)],
            videre.Column(
                [
                    self._search_input,
                    videre.Row(
                        [
                            videre.Button("AND", data="and", on_click=self._on_mode),
                            videre.Button("OR", data="or", on_click=self._on_mode),
                            videre.Button(
                                "Exact", data="exact", on_click=self._on_mode
                            ),
                            videre.Button("ID", data="id", on_click=self._on_mode),
                        ],
                        space=2,
                    ),
                    self._search_status,
                ],
                space=4,
            ),
        )

    def _sorting_section(self) -> Widget:
        return self._section(
            "Sorting",
            [
                videre.Button("⚙", on_click=self._open_sorting),
                videre.Button("✕", on_click=self._clear_sorting),
            ],
            self._sorting_display,
        )

    def _grouping_section(self) -> Widget:
        return self._section(
            "Grouping",
            [
                videre.Button("⚙", on_click=self._open_grouping),
                videre.Button("✕", on_click=self._clear_grouping),
            ],
            self._grouping_display,
        )

    def _groups_section(self) -> Widget:
        nav = videre.Row(
            [
                videre.Button("|<", on_click=self._group_first),
                videre.Button("<", on_click=self._group_prev),
                self._group_nav_label,
                videre.Button(">", on_click=self._group_next),
                videre.Button(">|", on_click=self._group_last),
            ],
            space=2,
            vertical_alignment=videre.Alignment.CENTER,
        )
        body = videre.Column(
            [
                nav,
                videre.Container(
                    videre.ScrollView(self._groups_column, wrap_horizontal=True),
                    height=220,
                    border=videre.Border.all(1, videre.Colors.lightgray),
                    padding=videre.Padding.all(4),
                ),
                self._add_classifier_holder,
            ],
            space=4,
        )
        return self._section("Groups", [], body)

    def _classifier_section(self) -> Widget:
        body = videre.Column(
            [
                self._classifier_column,
                videre.Button("Reverse", on_click=self._classifier_reverse),
            ],
            space=4,
        )
        return self._section("Classifier path", [], body)

    def _selection_section(self) -> Widget:
        self._selection_menu = videre.ContextButton("⚙", actions=[], square=True)
        return self._section(
            "Selection",
            [self._selection_menu, videre.Button("✕", on_click=self._clear_selection)],
            videre.Column(
                [
                    self._selection_label,
                    videre.Row(
                        [
                            videre.Button("Page", on_click=self._select_page),
                            videre.Button("All", on_click=self._select_all_in_view),
                        ],
                        space=4,
                    ),
                ],
                space=4,
            ),
        )

    def on_show(self) -> None:
        self._page_number = VIDEO_DEFAULT_PAGE_NUMBER
        self._reload()

    # --- public API (driven by the app shell) -------------------------------

    @property
    def page_size(self) -> int:
        return self._page_size

    @page_size.setter
    def page_size(self, size: int) -> None:
        # The setter owns the "resize => reset to page 0 + reload" rule, so the
        # app shell doesn't have to know it.
        self._page_size = size
        self._reset_and_reload()

    def refresh(self) -> None:
        """Reload the current view (used by the View > Refresh menu)."""
        self._reload()

    # --- data ---------------------------------------------------------------

    def _reload(self) -> None:
        selector = self._selector if self._show_only_selected else None
        self._context = self.context.get_videos(
            self._page_size, self._page_number, selector
        )
        ctx = self._context
        if ctx is None:
            self._cards.controls = [videre.Text("No database open.", italic=True)]
            self._status.text = ""
            self._page_label.text = ""
            self._sidebar_column.controls = [
                self._sec_sources,
                self._sec_search,
                self._sec_sorting,
                self._sec_grouping,
            ]
            return
        self._cards.controls = [
            VideoCard(video, index, self, self._selector.contains(video.video_id))
            for index, video in enumerate(ctx.result)
        ] or [videre.Text("(no video on this page)", italic=True)]
        self._view_count = ctx.selection_count
        self._update_selection_counter()
        self._refresh_selection_menu()
        self._status.text = (
            f"{ctx.selection_count} videos | "
            f"{ctx.selection_file_size} | {ctx.selection_duration}"
        )
        self._page_label.text = f"Page {ctx.page_number + 1} / {ctx.nb_pages or 1}"
        self._update_sources(ctx)
        self._update_search(ctx)
        self._update_sorting(ctx)
        self._update_grouping(ctx)

        sections = [
            self._sec_sources,
            self._sec_search,
            self._sec_sorting,
            self._sec_grouping,
            self._sec_selection,
        ]
        if ctx.grouping is not None and ctx.grouping.field is not None:
            self._populate_groups(ctx)
            sections.append(self._sec_groups)
        if ctx.classifier:
            self._populate_classifier(ctx)
            sections.append(self._sec_classifier)
        self._sidebar_column.controls = sections

    def _update_search(self, ctx) -> None:
        search = ctx.search
        if search is not None and getattr(search, "text", ""):
            self._search_status.text = f"'{search.text}' ({search.cond})"
        else:
            self._search_status.text = "(no search)"

    def _update_sources(self, ctx) -> None:
        expr = self.context.get_source_expression()
        if expr:
            self._sources_display.text = f"expr: {expr}"
        elif list(ctx.sources) == [["readable"]]:
            self._sources_display.text = "All readable"
        else:
            self._sources_display.text = (
                " ; ".join("/".join(path) for path in ctx.sources) or "(none)"
            )

    def _update_sorting(self, ctx) -> None:
        parts = []
        for item in ctx.sorting:
            reverse = item.startswith("-")
            field = item[1:] if item[:1] in "+-" else item
            info = FIELD_MAP.fields.get(field)
            parts.append(f"{info.title if info else field} {'▼' if reverse else '▲'}")
        self._sorting_display.text = ", ".join(parts) or "Default"

    def _update_grouping(self, ctx) -> None:
        # Own formatter, autonomous on purpose: a different display style from
        # pysaurus' pretty_grouping (which is also barely used elsewhere). Its
        # old crash on property fields has since been fixed in common.py.
        grouping = ctx.grouping
        if grouping is None or grouping.field is None:
            self._grouping_display.text = "No grouping"
            return
        if grouping.is_property:
            title = grouping.field
        else:
            info = FIELD_MAP.fields.get(grouping.field)
            title = info.title if info else grouping.field
        label = f"{title} {'▼' if grouping.reverse else '▲'}"
        if grouping.is_property:
            label = f"property: {label}"
        if grouping.sorting == "count":
            label = f"# {label}"
        elif grouping.sorting == "length":
            label = f"|| {label} ||"
        if grouping.allow_singletons:
            label = f"many {label}"
        self._grouping_display.text = label

    def _populate_groups(self, ctx) -> None:
        field = ctx.grouping.field
        stats = ctx.classifier_stats or []
        items = []
        for index, stat in enumerate(stats):
            label = f"{format_group_value(field, stat.value)} ({stat.count})"
            selected = index == (ctx.group_id or 0)
            items.append(
                videre.Div(
                    videre.Text(label, strong=selected, wrap=videre.TextWrap.WORD),
                    style={
                        "default": {
                            "background_color": theme.SELECTED_BG if selected else None
                        }
                    },
                    data=index,
                    on_click=self._on_group_click,
                )
            )
        self._groups_column.controls = items or [videre.Text("(no group)", italic=True)]
        current = (ctx.group_id or 0) + 1 if stats else 0
        self._group_nav_label.text = f"{current} / {len(stats)}"

        is_multiple = False
        if ctx.grouping.is_property:
            is_multiple = (
                len(self.context.get_prop_types(name=field, multiple=True)) > 0
            )
        self._add_classifier_holder.control = (
            videre.Button("✙ Add to classifier", on_click=self._on_add_classifier)
            if is_multiple
            else None
        )

    def _populate_classifier(self, ctx) -> None:
        path = list(ctx.classifier)
        badges = []
        for index, value in enumerate(path):
            row = [videre.Text(str(value))]
            if index == len(path) - 1:
                row.append(videre.Button("✕", on_click=self._classifier_unstack))
            badges.append(
                videre.Container(
                    videre.Row(
                        row, space=2, vertical_alignment=videre.Alignment.CENTER
                    ),
                    background_color=theme.BADGE_BG,
                    padding=videre.Padding.axis(vertical=2, horizontal=6),
                )
            )
        self._classifier_column.controls = badges

    # --- search -------------------------------------------------------------

    def _on_mode(self, widget) -> None:
        self.context.set_search(self._search_input.value, widget.data)
        self._reset_and_reload()

    def _clear_search(self, widget) -> None:
        self._search_input.value = ""
        self.context.set_search("", "and")
        self._reset_and_reload()

    # --- sorting ------------------------------------------------------------

    def _open_sorting(self, widget) -> None:
        sorting = list(self._context.sorting) if self._context else []
        dialog = SortingDialog(sorting)
        self.app.window.set_fancybox(
            dialog,
            title="Set Sorting",
            buttons=[
                videre.FancyCloseButton(
                    "Apply", data=dialog, on_click=self._apply_sorting
                ),
                videre.FancyCloseButton("Cancel"),
            ],
        )

    def _apply_sorting(self, widget) -> None:
        self.context.set_sorting(widget.data.get_result())
        self._reset_and_reload()

    def _clear_sorting(self, widget) -> None:
        self.context.set_sorting(list(VIDEO_DEFAULT_SORTING))
        self._reset_and_reload()

    # --- sources ------------------------------------------------------------

    def _open_sources(self, widget) -> None:
        current = list(self._context.sources) if self._context else []
        dialog = SourcesDialog(current, self.context.get_source_expression())
        self.app.window.set_fancybox(
            dialog,
            title="Select Sources",
            buttons=[
                videre.FancyCloseButton(
                    "Apply", data=dialog, on_click=self._apply_sources
                ),
                videre.FancyCloseButton("Cancel"),
            ],
        )

    def _apply_sources(self, widget) -> None:
        dialog = widget.data
        if dialog.is_advanced():
            self.context.set_source_expression(dialog.get_expression())
        else:
            self.context.set_sources(dialog.get_sources())
        self._reset_and_reload()

    def _clear_sources(self, widget) -> None:
        self.context.set_sources([])
        self._reset_and_reload()

    # --- grouping -----------------------------------------------------------

    def _open_grouping(self, widget) -> None:
        property_names = [prop.name for prop in self.context.get_prop_types()]
        current = self._context.grouping if self._context else None
        dialog = GroupingDialog(property_names, current)
        self.app.window.set_fancybox(
            dialog,
            title="Set Grouping",
            buttons=[
                videre.FancyCloseButton(
                    "Apply", data=dialog, on_click=self._apply_grouping
                ),
                videre.FancyCloseButton("Clear", on_click=self._clear_grouping),
                videre.FancyCloseButton("Cancel"),
            ],
        )

    def _apply_grouping(self, widget) -> None:
        result = widget.data.get_result()
        self.context.set_groups(
            result["field"],
            result["is_property"],
            result["sorting"],
            result["reverse"],
            result["allow_singletons"],
        )
        self._reset_and_reload()

    def _clear_grouping(self, widget) -> None:
        self.context.clear_groups()
        self._reset_and_reload()

    # --- groups & classifier ------------------------------------------------

    def _on_group_click(self, widget) -> None:
        self._select_group(widget.data)

    def _select_group(self, index: int) -> None:
        stats = self._context.classifier_stats if self._context else []
        if stats and 0 <= index < len(stats):
            self.context.set_group(index)
            self._reset_and_reload()

    def _group_first(self, widget) -> None:
        self._select_group(0)

    def _group_prev(self, widget) -> None:
        self._select_group((self._context.group_id or 0) - 1 if self._context else 0)

    def _group_next(self, widget) -> None:
        self._select_group((self._context.group_id or 0) + 1 if self._context else 0)

    def _group_last(self, widget) -> None:
        stats = self._context.classifier_stats if self._context else []
        self._select_group(len(stats) - 1)

    def _on_add_classifier(self, widget) -> None:
        if self._context:
            self.context.classifier_select_group(self._context.group_id or 0)
            self._reset_and_reload()

    def _classifier_unstack(self, widget) -> None:
        self.context.classifier_back()
        self._reset_and_reload()

    def _classifier_reverse(self, widget) -> None:
        self.context.classifier_reverse()
        self._reset_and_reload()

    # --- selection (phase 5b) -----------------------------------------------

    def _update_selection_counter(self) -> None:
        count = self._selector.size_from(self._view_count)
        self._selection_label.text = f"{count} selected" if count else "no selection"

    def _on_card_check(self, checkbox) -> None:
        video_id = checkbox.data
        if checkbox.checked:
            self._selector.include(video_id)
        else:
            self._selector.exclude(video_id)
        self._update_selection_counter()

    def _select_page(self, widget) -> None:
        if self._context:
            for video in self._context.result:
                self._selector.include(video.video_id)
            self._reload()

    def _select_all_in_view(self, widget) -> None:
        self._selector.select_all()
        self._reload()

    def _clear_selection(self, widget=None) -> None:
        self._selector.deselect_all()
        was_show_only = self._show_only_selected
        self._show_only_selected = False
        if was_show_only:
            self._reset_and_reload()
        else:
            self._reload()

    def _selected_ids(self) -> set:
        """Explicit selected video ids. In 'All' (exclude) mode we can only
        enumerate the current page reliably — a noted v1 limitation."""
        selection = self._selector.to_dict()
        if not selection["all"]:
            return set(selection["include"])
        return {
            video.video_id
            for video in (self._context.result if self._context else [])
            if self._selector.contains(video.video_id)
        }

    def _refresh_selection_menu(self) -> None:
        if self._selection_menu is None:
            return
        check = "☑" if self._show_only_selected else "☐"
        actions = [
            (f"{check} Show only selected", self._toggle_show_only_selected),
            ("Toggle watched on selection", self._selection_toggle_watched),
            ("Delete selection from database", self._delete_selected),
        ]
        for prop in self.context.get_prop_types():
            actions.append(
                (
                    f"Edit property: {prop.name}",
                    lambda p=prop: self._edit_property_for_selection(p),
                )
            )
        self._selection_menu.actions = actions

    def _toggle_show_only_selected(self) -> None:
        if (
            not self._show_only_selected
            and self._selector.size_from(self._view_count) == 0
        ):
            return
        self._show_only_selected = not self._show_only_selected
        self._reset_and_reload()

    def _selection_toggle_watched(self) -> None:
        ids = self._selected_ids()
        if ids:
            self.context.toggle_watched_many(ids)
            self._reload()

    def _delete_selected(self) -> None:
        ids = self._selected_ids()
        if not ids:
            return
        self.app.window.confirm(
            f"Delete {len(ids)} video(s) from the database? "
            "(Files are NOT deleted from disk)",
            "Delete selection",
            on_confirm=lambda: self._do_delete_selected(ids),
        )

    def _do_delete_selected(self, ids) -> None:
        self.context.delete_video_entries(ids)
        self._clear_selection()

    def _edit_property_for_selection(self, prop) -> None:
        selector_dict = self._selector.to_dict()
        count = self._selector.size_from(self._view_count)
        values_and_counts = (
            self.context.call_on_view(selector_dict, "count_property_values", prop.name)
            or []
        )
        dialog = BatchEditPropertyDialog(prop, count, values_and_counts)
        prop_name = prop.name
        self.app.window.set_fancybox(
            dialog,
            title=f"Edit property: {prop_name}",
            buttons=[
                videre.FancyCloseButton(
                    "Apply",
                    on_click=lambda w: self._apply_batch_edit(
                        prop_name, selector_dict, dialog
                    ),
                ),
                videre.FancyCloseButton("Cancel"),
            ],
        )

    def _apply_batch_edit(self, prop_name, selector_dict, dialog) -> None:
        to_add, to_remove = dialog.get_changes()
        if to_add or to_remove:
            self.context.call_on_view(
                selector_dict, "edit_property_for_videos", prop_name, to_add, to_remove
            )
            self._reload()

    # --- video actions (phase 5a) -------------------------------------------

    def video_toggle_watched(self, video) -> None:
        self.context.toggle_watched(video.video_id)
        self._reload()

    def video_open(self, video) -> None:
        self.context.open_video(video.video_id)

    def video_open_folder(self, video) -> None:
        self.context.open_containing_folder(video.video_id)

    def video_copy(self, video, field: str) -> None:
        pyperclip.copy(str(getattr(video, field)))

    def video_rename(self, video) -> None:
        entry = videre.TextInput(str(video.file_title))
        self.app.window.set_fancybox(
            videre.Column(
                [videre.Text(str(video.filename), wrap=videre.TextWrap.CHAR), entry],
                space=8,
            ),
            title="Rename video",
            buttons=[
                videre.FancyCloseButton(
                    "Rename", on_click=lambda w: self._do_rename(video, entry)
                ),
                videre.FancyCloseButton("Cancel"),
            ],
        )

    def _do_rename(self, video, entry) -> None:
        self.context.rename_video(video.video_id, entry.value)
        self._reload()

    def video_delete_entry(self, video) -> None:
        # Mirror pyside6: a "not found" entry (file gone from disk) is removed
        # without confirmation when the option is disabled.
        if not video.found and not self.confirm_not_found_deletion:
            self._run_video_action(self.context.delete_video_entry, video)
            return
        self._confirm_video(
            f"Delete '{video.filename}' from database?",
            "Delete from database",
            self.context.delete_video_entry,
            video,
        )

    def video_trash(self, video) -> None:
        self._confirm_video(
            f"Move '{video.filename}' to trash?",
            "Move to Trash",
            self.context.trash_video,
            video,
        )

    def video_delete_file(self, video) -> None:
        self._confirm_video(
            f"Permanently delete '{video.filename}'?",
            "Delete permanently",
            self.context.delete_video_file,
            video,
        )

    def _confirm_video(self, message, title, action, video) -> None:
        self.app.window.confirm(
            message, title, on_confirm=lambda: self._run_video_action(action, video)
        )

    def _run_video_action(self, action, video) -> None:
        action(video.video_id)
        self._reload()

    # --- pagination ---------------------------------------------------------

    def _nb_pages(self) -> int:
        return (self._context.nb_pages or 1) if self._context else 1

    def _reset_and_reload(self) -> None:
        self._page_number = VIDEO_DEFAULT_PAGE_NUMBER
        self._reload()

    def _goto(self, page: int) -> None:
        page = max(0, min(page, self._nb_pages() - 1))
        if page != self._page_number:
            self._page_number = page
            self._reload()

    def _first(self, widget) -> None:
        self._goto(0)

    def _prev(self, widget) -> None:
        self._goto(self._page_number - 1)

    def _next(self, widget) -> None:
        self._goto(self._page_number + 1)

    def _last(self, widget) -> None:
        self._goto(self._nb_pages() - 1)
