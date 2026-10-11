"""Render every Kyuti page, dialog and notable state to PNG, for UI review.

Runs on the test database ``example_db_in_pysaurus`` (copied in memory, never
written on disk) under ``tests/home_dir_test``, so no real database is read.
No window ever appears: widgets get ``WA_DontShowOnScreen`` before ``show()``
and are rendered with ``grab()`` on the real platform plugin, so the PNGs have
the native look at the screen's scale factor.

    uv run -m pysaurus.scripts.capture_kyuti [--out DIR] [--lang CODE]

Default output: ``ignored/kyuti_audit/<lang>/``.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, cast
from unittest.mock import patch

from PySide6.QtCore import QBuffer, QCoreApplication, QEvent, QIODevice, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QInputDialog,
    QLineEdit,
    QMenu,
    QMessageBox,
    QTabWidget,
)

from pysaurus.application.application import Application
from pysaurus.core import language
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.classes import Selector
from pysaurus.core.job_notifications import JobStep, JobToDo
from pysaurus.core.language import say
from pysaurus.core.notifications import (
    DatabaseReady,
    Message,
    ProfilingEnd,
    ProfilingStart,
)
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.database.algorithms.folder_scan import (
    EMPTY_FOLDER_EXT,
    FileInfo,
    FolderScanProgress,
    FolderScanResult,
)
from pysaurus.dbview.view_context import ViewContext
from pysaurus.interface.api.feature_api import FeatureAPI
from pysaurus.interface.kyuti.app_context import AppContext
from pysaurus.interface.kyuti.dialogs.batch_edit_property_dialog import (
    BatchEditPropertyDialog,
)
from pysaurus.interface.kyuti.dialogs.batch_redundant_values_dialog import (
    BatchRedundantValuesDialog,
)
from pysaurus.interface.kyuti.dialogs.database_settings_dialog import (
    DatabaseSettingsDialog,
)
from pysaurus.interface.kyuti.dialogs.edit_folders_dialog import EditFoldersDialog
from pysaurus.interface.kyuti.dialogs.fill_property_dialog import FillPropertyDialog
from pysaurus.interface.kyuti.dialogs.goto_duration_dialog import GoToDurationDialog
from pysaurus.interface.kyuti.dialogs.goto_page_dialog import GoToPageDialog
from pysaurus.interface.kyuti.dialogs.grouping_dialog import GroupingDialog
from pysaurus.interface.kyuti.dialogs.move_values_dialog import MoveValuesDialog
from pysaurus.interface.kyuti.dialogs.process_dialog import ProcessDialog
from pysaurus.interface.kyuti.dialogs.property_values_dialog import PropertyValuesDialog
from pysaurus.interface.kyuti.dialogs.redundant_values_dialog import (
    RedundantValuesDialog,
)
from pysaurus.interface.kyuti.dialogs.rename_dialog import RenameDialog
from pysaurus.interface.kyuti.dialogs.replace_video_dialog import ReplaceVideoDialog
from pysaurus.interface.kyuti.dialogs.sorting_dialog import SortingDialog
from pysaurus.interface.kyuti.dialogs.sources_dialog import SourcesDialog
from pysaurus.interface.kyuti.dialogs.video_confirm_dialog import VideoConfirmDialog
from pysaurus.interface.kyuti.dialogs.video_properties_dialog import (
    VideoPropertiesDialog,
)
from pysaurus.interface.kyuti.main import _setup_scaled_font
from pysaurus.interface.kyuti.main_window import MainWindow, SessionLogDialog
from pysaurus.interface.kyuti.pages.process_page import ProcessPage
from pysaurus.interface.kyuti.widgets.left_click_menu import LeftClickMenu
from pysaurus.interface.kyuti.widgets.video_list_item import VideoListItem
from tests.utils import get_saurus_sql_database

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
TEST_HOME_DIR = os.path.join(PROJECT_ROOT, "tests", "home_dir_test")
EXAMPLE_DB = os.path.join(
    TEST_HOME_DIR, ".Pysaurus", "databases", "example_db_in_pysaurus"
)

WINDOW_SIZE = (1200, 800)


class TestHomeApplication(Application):
    """An Application whose home is the test home dir, not the user's."""

    def __init__(self, notifier):
        super().__init__(notifier, home_dir=TEST_HOME_DIR)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render every Kyuti page, dialog and notable state to PNG."
    )
    parser.add_argument("--out", default=None, help="output directory")
    parser.add_argument("--lang", default="en", help="language code (en, fr)")
    args = parser.parse_args()
    out = args.out or os.path.join(PROJECT_ROOT, "ignored", "kyuti_audit", args.lang)
    os.makedirs(out, exist_ok=True)

    app = QApplication(sys.argv)
    app.setApplicationName("Pysaurus")
    capture = Capture(app, out, args.lang)
    capture.run()
    print(f"{capture.count} images written to {out}")


class Capture:
    def __init__(self, app, out: str, lang: str):
        self.app = app
        self.out = out
        self.lang = lang
        self.count = 0
        self.scan_result: FolderScanResult | None = None

    # ------------------------------------------------------------------ setup

    def run(self) -> None:
        _setup_scaled_font(self.app)

        with patch("pysaurus.interface.kyuti.app_context.KyutiAPI"):
            ctx = AppContext()
        with patch(
            "pysaurus.interface.api.feature_api.Application", TestHomeApplication
        ):
            api = FeatureAPI(DEFAULT_NOTIFIER)
        api.application.config.language = self.lang
        language.set_language(self.lang)
        # A plain FeatureAPI stands in for KyutiAPI: no Flask server, no threads.
        patched = cast(Any, ctx)
        patched._api = api
        ctx._qt_translations.apply(self.lang)
        # FeatureAPI has no scan support (it lives in GuiAPI): shadow the facade
        # method so the files page can be rendered with a fabricated result.
        patched.get_last_scan_result = lambda: self.scan_result
        self.ctx = ctx

        with patch("pysaurus.interface.kyuti.main_window.AppContext", lambda: ctx):
            self.window = MainWindow()
        self.window.resize(*WINDOW_SIZE)
        self.show(self.window)

        self.snap(self.window, "01_databases_page")
        self.capture_databases_page_expanded()

        self.db = get_saurus_sql_database(EXAMPLE_DB)
        self.prepare_data()
        api.database = self.db
        self.window._update_database_menu_state()
        self.window.show_videos_page()
        self.settle()

        self.capture_videos_page_states()
        self.capture_menus()
        self.capture_video_context_menu()
        self.capture_videos_dialogs()
        self.capture_properties_page()
        self.capture_files_page()
        self.capture_process_page()
        self.capture_message_boxes()

    def prepare_data(self) -> None:
        """Enrich the in-memory copy so every display path has something to show."""
        videos = self.db.get_videos()
        # Videos of the first page of the default view come first, so that the
        # enriched ones are visible without navigating.
        first_page = {
            v.video_id for v in self.db.query_videos(ViewContext(), 20, 0).result
        }
        found = [v for v in videos if v.found and v.readable]
        found.sort(key=lambda v: (v.video_id not in first_page, v.video_id))
        # Fake thumbnails: a colored frame with the video id, like a real one
        # would fill the slot in the list items.
        rows = []
        for i, video in enumerate(found):
            image = QImage(320, 180, QImage.Format.Format_RGB32)
            image.fill(QColor.fromHsv((i * 37) % 360, 90, 200))
            painter = QPainter(image)
            painter.setPen(Qt.GlobalColor.white)
            painter.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
            painter.drawText(
                image.rect(), Qt.AlignmentFlag.AlignCenter, f"#{video.video_id}"
            )
            painter.end()
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            # The stub wants bytes, the runtime only accepts str.
            image.save(buffer, "JPEG", 80)  # ty: ignore[no-matching-overload]
            rows.append((video.video_id, buffer.data().data()))
        self.db.db.modify_many(
            "INSERT OR REPLACE INTO video_thumbnail (video_id, thumbnail) VALUES (?, ?)",
            rows,
        )
        # Similarity groups: three groups of three, one dismissed, one re-encoded pair.
        ids = [v.video_id for v in found]
        self.db.ops.set_similarities_from_list(
            ids[:9] + [ids[9]], [1, 1, 1, 2, 2, 2, 3, 3, 3, -1]
        )
        self.db.ops.set_similarities_from_list(
            ids[10:12], [7, 7], field="similarity_id_reencoded"
        )
        # Some watched videos and a few property values.
        for video_id in ids[2:6]:
            self.db.ops.mark_as_watched(video_id)
        self.db.video_entry_set_tags(ids[0], {"appreciation": [4.5], "has sky": [True]})
        self.db.video_entry_set_tags(ids[1], {"title": ["My favourite clip"]})
        self.db.ops.save_search("width > 100 and found", "Wide and found")
        self.db.ops.save_search('"mkv" in `category`')
        self.similarity_ids = ids[:9]
        self.sample_video_id = ids[0]

    # --------------------------------------------------------------- helpers

    def show(self, widget) -> None:
        widget.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        widget.show()
        self.settle()

    def settle(self, rounds: int = 6) -> None:
        for _ in range(rounds):
            self.app.processEvents()
            # Widgets replaced by setItemWidget() are deleteLater()'d: without
            # this they linger as ghosts behind their successors in the grab.
            QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def snap(self, widget, name: str) -> None:
        self.settle()
        path = os.path.join(self.out, f"{name}.png")
        widget.grab().save(path)
        self.count += 1
        print("wrote", name)

    def snap_dialog(self, dialog, name: str, size=None) -> None:
        if size:
            dialog.resize(*size)
        self.show(dialog)
        self.snap(dialog, name)
        dialog.close()
        dialog.deleteLater()
        self.settle()

    def snap_menu(self, menu, name: str) -> None:
        """Render a QMenu and each of its submenus."""
        menu.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        menu.popup(self.window.mapToGlobal(self.window.rect().center()))
        self.settle()
        self.snap(menu, name)
        # Never go through QAction.menu(): in PySide6 6.11 it hands the submenu
        # over to Python, which then destroys the C++ object.
        for sub in menu.findChildren(
            QMenu, options=Qt.FindChildOption.FindDirectChildrenOnly
        ):
            label = sub.title().replace("&", "").replace("...", "")
            label = "".join(c if c.isalnum() else "_" for c in label).strip("_")
            self.snap_menu(sub, f"{name}__{label}")
        menu.hide()
        self.settle()

    def menu_catcher(self, name: str):
        """Patch LeftClickMenu.exec to render the menu instead of running it."""
        capture = self

        def fake_exec(menu, *args, **kwargs):
            capture.snap_menu(menu, name)
            return None

        return patch.object(LeftClickMenu, "exec", fake_exec)

    def group_by(self, field: str, **options) -> None:
        settings = {
            "is_property": False,
            "sorting": "field",
            "reverse": False,
            "allow_singletons": False,
        }
        settings.update(options)
        self.ctx.set_groups(field=field, **settings)
        self.settle()

    # --------------------------------------------------------------- pages

    def capture_databases_page_expanded(self) -> None:
        page = self.window.databases_page
        if page._db_widgets:
            page._db_widgets[0].toggle_expanded()
            page.name_input.setText("my new collection")
            page.sources_list.addItem("📁 D:\\Videos\\Holidays")
            page.sources_list.addItem("📄 D:\\Videos\\single_file.mp4")
            self.snap(self.window, "02_databases_page_expanded")
            page._db_widgets[0].collapse()
            page.name_input.clear()
            page.sources_list.clear()

    def capture_videos_page_states(self) -> None:
        page = self.window.videos_page
        self.snap(self.window, "10_videos_default")

        # Larger window, like a maximized screen.
        self.window.resize(1700, 1000)
        self.settle()
        self.snap(self.window, "11_videos_default_wide")
        self.window.resize(*WINDOW_SIZE)
        self.settle()

        # A page-wide selection.
        page._select_all()
        self.settle()
        self.snap(self.window, "12_videos_selection")
        page._clear_selection()
        self.settle()

        # Search active (AND mode); this one matches nothing.
        page.search_input.setText("mkv")
        page._do_search("and")
        self.settle()
        self.snap(self.window, "12b_videos_search_empty")
        page._clear_search()
        self.settle()
        page.search_input.setText("natural")
        page._do_search("or")
        self.settle()
        self.snap(self.window, "12c_videos_search_or")
        page._clear_search()
        self.settle()

        # Source expression active + custom sorting.
        self.ctx.set_source_expression("width > 100 and found")
        self.ctx.set_sorting(["+length", "-size"])
        self.settle()
        self.snap(self.window, "13_videos_expression_and_sorting")
        self.ctx.set_source_expression(None)
        self.ctx.set_sorting(None)
        self.settle()

        # Problem sources only: not-found and unreadable videos.
        self.ctx.set_sources([["readable", "not_found"], ["unreadable"]])
        self.settle()
        self.snap(self.window, "14_videos_problem_sources")
        self.ctx.set_sources(None)
        self.settle()

        # Grouped by a multiple property (classifier available), then a path.
        self.group_by(
            "category",
            is_property=True,
            sorting="count",
            reverse=True,
            allow_singletons=True,
        )
        self.snap(self.window, "15_videos_grouped_by_category")
        page._on_classifier_add_group()
        self.settle()
        self.snap(self.window, "16_videos_classifier_path")
        self.ctx.clear_groups()
        self.settle()

        # Grouped by an attribute, singletons excluded.
        self.group_by("extension")
        self.snap(self.window, "17_videos_grouped_by_extension")
        self.ctx.clear_groups()
        self.settle()

        # Grouped by similarity: diff highlights and generalize actions.
        self.group_by("similarity_id")
        self.snap(self.window, "18_videos_grouped_by_similarity")

        # Grouped by move_id: the confirm-unique-moves button.
        self.group_by("move_id", allow_singletons=True)
        self.snap(self.window, "19_videos_grouped_by_moves")
        self.ctx.clear_groups()
        self.settle()

        # Single list item at a few widths.
        video = self.ctx.get_video_by_id(self.sample_video_id)
        assert video is not None
        for width in (500, 900):
            item = VideoListItem(video)
            item.resize(width, item.heightForWidth(width))
            self.show(item)
            self.snap(item, f"20_list_item_w{width}")
            item.close()
        item = VideoListItem(
            video,
            diff_fields={"file_title", "size", "length", "date"},
            file_title_diffs=[(0, 1)],
        )
        item.selected = True
        item.resize(900, item.heightForWidth(900))
        self.show(item)
        self.snap(item, "21_list_item_selected_diffs")
        item.close()

    def capture_menus(self) -> None:
        self.snap_menu(self.window.database_menu, "30_menu_database")
        self.snap_menu(self.window.view_menu, "31_menu_view")
        self.snap_menu(self.window.options_menu, "32_menu_options")
        self.snap_menu(self.window.help_menu, "33_menu_help")
        page = self.window.videos_page
        page._select_all()
        self.settle()
        with self.menu_catcher("34_menu_selection"):
            page._on_selection_menu()
        page._clear_selection()
        self.settle()

    def capture_video_context_menu(self) -> None:
        page = self.window.videos_page
        # Plain video (no grouping).
        with self.menu_catcher("35_context_menu_video"):
            page._on_video_context_menu(self.sample_video_id, None)
        # Inside a similarity group: dismiss/reset, generalize, copy, replace.
        self.group_by("similarity_id")
        with self.menu_catcher("36_context_menu_similarity"):
            page._on_video_context_menu(self.similarity_ids[0], None)
        self.ctx.clear_groups()
        self.settle()

    def capture_videos_dialogs(self) -> None:
        ctx = self.ctx
        parent = self.window
        prop_types = ctx.get_prop_types()
        video = ctx.get_video_by_id(self.sample_video_id)
        assert video is not None

        self.snap_dialog(
            SourcesDialog(None, None, parent, start_tab=0, ctx=ctx), "40_sources_simple"
        )
        self.snap_dialog(
            SourcesDialog(None, "width > 100 and found", parent, start_tab=1, ctx=ctx),
            "41_sources_advanced_saved",
        )
        dialog = SourcesDialog(None, "width >", parent, start_tab=1, ctx=ctx)
        dialog._show_expression_error(
            "Invalid expression: unexpected end of input at position 7"
        )
        self.snap_dialog(dialog, "42_sources_advanced_error")

        self.snap_dialog(GroupingDialog(prop_types, None, parent), "43_grouping")
        self.snap_dialog(
            GroupingDialog(
                prop_types,
                {
                    "field": "category",
                    "is_property": True,
                    "sorting": "count",
                    "reverse": True,
                    "allow_singletons": True,
                },
                parent,
            ),
            "44_grouping_property",
        )
        self.snap_dialog(
            SortingDialog([("date", True), ("size", False), ("title", False)], parent),
            "45_sorting",
        )
        self.snap_dialog(SortingDialog([], parent), "46_sorting_empty")
        self.snap_dialog(GoToPageDialog(2, 5, parent), "47_goto_page")
        self.snap_dialog(GoToDurationDialog(True, parent), "48_goto_duration")
        self.snap_dialog(
            VideoPropertiesDialog(video, prop_types, ctx, parent),
            "49_video_properties",
            size=(700, 600),
        )
        dialog = VideoPropertiesDialog(video, prop_types, ctx, parent)
        self.show(dialog)
        # Simulate edits: modified single value and a cleared one.
        cast(QLineEdit, dialog._property_widgets["title"]).setText("Edited title")
        dialog._on_widget_changed("title")
        dialog._on_clear_property("appreciation")
        dialog.resize(700, 600)
        self.snap(dialog, "50_video_properties_edited")
        dialog.close()
        dialog = VideoPropertiesDialog(video, prop_types, ctx, parent)
        self.show(dialog)
        tabs = dialog.findChildren(QTabWidget)
        if tabs:
            tabs[0].setCurrentIndex(1)
        dialog.resize(700, 600)
        self.snap(dialog, "51_video_properties_info_tab")
        dialog.close()

        everything = Selector(True, set()).to_dict()
        values = ctx.query_on_view(everything, "count_property_values", "category")
        cat = next(p for p in prop_types if p.name == "category")
        self.snap_dialog(
            BatchEditPropertyDialog("category", cat, 90, values or [], parent),
            "52_batch_edit_multiple",
        )
        nature = next(p for p in prop_types if p.name == "is nature")
        values = ctx.query_on_view(everything, "count_property_values", "is nature")
        self.snap_dialog(
            BatchEditPropertyDialog("is nature", nature, 90, values or [], parent),
            "53_batch_edit_enum_single",
        )
        sky = next(p for p in prop_types if p.name == "has sky")
        self.snap_dialog(
            BatchEditPropertyDialog("has sky", sky, 3, [[True, 2], [False, 1]], parent),
            "54_batch_edit_bool",
        )

        in_path = ctx.find_redundant_property_values(
            [self.sample_video_id], use_full_path=True
        )
        in_title = ctx.find_redundant_property_values([self.sample_video_id])
        self.snap_dialog(
            RedundantValuesDialog(
                video,
                prop_types,
                in_path.get(self.sample_video_id, {}),
                in_title.get(self.sample_video_id, {}),
                parent,
            ),
            "55_redundant_values",
        )
        self.snap_dialog(
            BatchRedundantValuesDialog(
                3,
                {1: {"category": ["a", "mkv"]}, 2: {"category": ["b"]}},
                {1: {"category": ["a"]}},
                parent,
            ),
            "56_batch_redundant_values",
        )
        self.snap_dialog(
            VideoConfirmDialog(
                say("Move to Trash"),
                say(
                    "Move this video to the system trash?\n\n"
                    "(The file can be restored from the trash if needed)"
                ),
                video,
                parent,
            ),
            "57_video_confirm_trash",
        )
        self.snap_dialog(
            ReplaceVideoDialog(video, "other_clip", None, parent), "58_replace_video"
        )
        self.snap_dialog(
            ReplaceVideoDialog(
                video,
                "other_clip",
                "No property is configured for generalized titles, "
                "so the titles cannot be copied.",
                parent,
            ),
            "59_replace_video_note",
        )
        self.snap_dialog(
            RenameDialog(
                say("Rename Database: {name}", name="example_db_in_pysaurus"),
                "example_db_in_pysaurus",
                say("New database name:"),
                parent,
            ),
            "60_rename_database",
        )
        self.snap_dialog(
            EditFoldersDialog(
                ctx.get_database_folders() + ["D:\\Videos\\More"],
                "example_db_in_pysaurus",
                parent,
            ),
            "61_edit_folders",
        )
        self.snap_dialog(
            DatabaseSettingsDialog(
                ctx.get_database_settings(),
                ["category", "title"],
                "example_db_in_pysaurus",
                parent,
            ),
            "62_database_settings",
        )
        self.snap_dialog(
            SessionLogDialog(
                self.window._session_log
                + [
                    "[2026-10-11 10:00:00] 'a' moved to trash",
                    "[2026-10-11 10:00:05] Watched status toggled for 3 video(s)",
                ],
                parent,
            ),
            "63_session_log",
        )
        # QInputDialog as used for rename video / concatenate path.
        dialog = QInputDialog(parent)
        dialog.setWindowTitle(say("Rename Video"))
        dialog.setLabelText(say("New file title:"))
        dialog.setTextValue("a")
        dialog.setTextEchoMode(QLineEdit.EchoMode.Normal)
        self.snap_dialog(dialog, "64_rename_video_input")
        dialog = QInputDialog(parent)
        dialog.setWindowTitle(say("Concatenate Path"))
        dialog.setLabelText(
            say("Select target property to concatenate path values into:")
        )
        dialog.setComboBoxItems(["title"])
        dialog.setOption(
            QInputDialog.InputDialogOption.UseListViewForComboBoxItems, False
        )
        self.snap_dialog(dialog, "65_concatenate_path_input")
        # Generalize title target dialog is built inline in VideosPage.
        page = self.window.videos_page

        def fake_exec(dialog):
            self.show(dialog)
            self.snap(dialog, "66_generalize_title_target")
            dialog.close()
            return 0

        with patch.object(QDialog, "exec", fake_exec):
            page._view_count = 4
            page._ask_generalize_title_target("Some title")

    def capture_properties_page(self) -> None:
        self.window.show_properties_page()
        self.settle()
        self.snap(self.window, "70_properties_page")
        page = self.window.properties_page
        # Form filled: enum type.
        page.name_input.setText("genre")
        page.type_combo.setCurrentText("str")
        page.enum_check.setChecked(True)
        page.enum_input.setText("action, drama, comedy")
        self.snap(self.window, "71_properties_page_enum_form")
        page._reset_form()
        page.type_combo.setCurrentText("bool")
        self.snap(self.window, "72_properties_page_bool_form")
        page._reset_form()
        # Actions menu of the first row (appreciation: float single) and of the
        # second (category: str multiple).
        for row, name in (
            (0, "73_properties_actions_menu"),
            (1, "74_properties_actions_menu_multiple"),
        ):
            widget = page.props_table.cellWidget(row, 5)
            menu = widget.findChild(QMenu) if widget else None
            if menu is not None:
                self.snap_menu(menu, name)

        prop_types = self.ctx.get_prop_types()
        cat = next(p for p in prop_types if p.name == "category")
        self.snap_dialog(
            PropertyValuesDialog("category", cat, self.ctx, self.window),
            "75_property_values",
        )
        appreciation = next(p for p in prop_types if p.name == "appreciation")
        self.snap_dialog(
            PropertyValuesDialog("appreciation", appreciation, self.ctx, self.window),
            "76_property_values_float",
        )
        self.snap_dialog(
            MoveValuesDialog(cat, prop_types, self.ctx, self.window), "77_move_values"
        )
        self.snap_dialog(
            FillPropertyDialog(prop_types, self.window), "78_fill_property"
        )
        self.snap_dialog(FillPropertyDialog([], self.window), "79_fill_property_none")
        self.window.show_videos_page()
        self.settle()

    def capture_files_page(self) -> None:
        self.window.show_files_page()
        self.settle()
        self.snap(self.window, "80_files_page_empty")

        def info(path, size):
            ext = os.path.splitext(path)[1][1:]
            return FileInfo(path=AbsolutePath(path), extension=ext, size=size)

        result = FolderScanResult(
            others={
                "jpg": [
                    info(f"D:\\Videos\\thumbs\\img{i}.jpg", 50_000 + i)
                    for i in range(12)
                ],
                "nfo": [info("D:\\Videos\\movie.nfo", 1200)],
                "part": [info("D:\\Videos\\incomplete.part", 700_000_000)],
                "": [info("D:\\Videos\\README", 300)],
                EMPTY_FOLDER_EXT: [info("D:\\Videos\\old", 0)],
            },
            videos_indexed={
                "mkv": [
                    info(f"D:\\Videos\\v{i}.mkv", 1_000_000_000) for i in range(40)
                ],
                "mp4": [info(f"D:\\Videos\\m{i}.mp4", 500_000_000) for i in range(30)],
            },
            videos_unknown={"mp4": [info("D:\\Videos\\new.mp4", 800_000_000)]},
        )
        self.scan_result = result
        self.window.files_page.refresh()
        self.settle()
        self.snap(self.window, "81_files_page_others")
        self.window.files_page._tabs.setCurrentIndex(1)
        self.settle()
        self.snap(self.window, "82_files_page_video_stats")
        self.window.files_page._tabs.setCurrentIndex(0)
        self.scan_result = None
        self.window.show_videos_page()
        self.settle()

    def capture_process_page(self) -> None:
        page = ProcessPage("Updating Database")
        page.resize(*WINDOW_SIZE)
        self.show(page)
        page.on_notification(ProfilingStart("Collect videos"))
        page.on_notification(FolderScanProgress(12, 40, 3500))
        page.on_notification(JobToDo("collect", 3500, "Collecting video infos"))
        for step in range(0, 2100, 300):
            page.on_notification(JobStep("collect", None, step, 3500))
        page.on_notification(JobToDo("thumbs", 900, "Generating thumbnails"))
        page.on_notification(JobStep("thumbs", "0", 300, 900))
        page.on_notification(Message("3 videos could not be read"))
        self.snap(page, "90_process_running")
        page.on_notification(ProfilingEnd("Collect videos", "0:00:42"))
        page.on_notification(DatabaseReady("Database updated"))
        self.snap(page, "91_process_done")
        page.close()

        dialog = ProcessDialog("Moving Video", parent=self.window)
        self.show(dialog)
        dialog.page.on_notification(JobToDo("move", 100, "Moving file"))
        dialog.page.on_notification(JobStep("move", None, 60, 100))
        self.snap(dialog, "92_process_dialog")
        dialog.hide()
        dialog.deleteLater()

    def capture_message_boxes(self) -> None:
        box = QMessageBox(
            QMessageBox.Icon.Question,
            say("Delete Videos"),
            say(
                "Delete {count} video(s) from the database?\n\n"
                "(Files will NOT be deleted from disk)",
                count=3,
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            self.window,
        )
        self.snap_dialog(box, "95_msg_delete_videos")
        box = QMessageBox(
            QMessageBox.Icon.Question,
            say("Quit"),
            say("Are you sure you want to quit?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            self.window,
        )
        self.snap_dialog(box, "96_msg_quit")
        box = QMessageBox(
            QMessageBox.Icon.Critical,
            say("Fatal Error"),
            say(
                "An unexpected error occurred:\n\n{name}: {message}",
                name="RuntimeError",
                message="something broke",
            ),
            QMessageBox.StandardButton.Ok,
            self.window,
        )
        box.setDetailedText("Traceback (most recent call last):\n  ...")
        self.snap_dialog(box, "97_msg_fatal")


if __name__ == "__main__":
    main()
