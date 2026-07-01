"""Coverage for the Databases page: list/expand, open/update/delete, sources,
create. Backend calls (get_database_names / run_process / delete) are mocked, so
no real Application or threaded op is needed."""

import pytest
import videre

from pysaurus.interface.videroid import theme
from tests.interface.videroid_interface._widget_tree import find as _find


def _evt(**attrs):
    return type("Evt", (), attrs)()


@pytest.fixture
def db_page(videroid_app, monkeypatch):
    app, window = videroid_app
    monkeypatch.setattr(
        app.context, "get_database_names", lambda: ["test_database", "db2"]
    )
    app.show_page("databases")
    window.render()
    return app, window, app._pages["databases"]


class TestDatabaseList:
    def test_toggle_expand_collapse(self, db_page):
        _, _, page = page_and(db_page)
        page._on_toggle(_evt(data="db2"))
        assert page._expanded == "db2"
        page._populate_databases()  # renders the expanded item (Open/Update/Delete)
        page._on_toggle(_evt(data="db2"))  # collapse
        assert page._expanded is None

    def test_open(self, db_page, monkeypatch):
        app, _, page = page_and(db_page)
        calls = []
        monkeypatch.setattr(app, "run_process", lambda *a: calls.append(a))
        page._on_open(_evt(data="db2"))
        assert calls and calls[0][0] == "Opening 'db2'"  # right process title

    def test_update_confirms(self, db_page):
        app, _, page = page_and(db_page)
        page._on_update(_evt(data="db2"))  # opens an "Update Database" confirm
        assert app.window.has_fancybox()

    def test_after_database_ready_with_db_goes_to_videos(self, db_page):
        app, _, page = page_and(db_page)
        assert app.context.has_database()
        page._after_database_ready(None)  # db open -> show its videos
        assert app._current == "videos"

    def test_delete(self, db_page, monkeypatch):
        app, _, page = page_and(db_page)
        deleted = []
        monkeypatch.setattr(app.context, "delete_database", deleted.append)
        page._expanded = "db2"
        page._on_delete(_evt(data="db2"))  # confirm fancybox
        page._delete("db2")
        assert deleted == ["db2"] and page._expanded is None


class TestSources:
    def test_add_and_dedup(self, db_page):
        _, _, page = page_and(db_page)
        page._add_source("/some/folder")
        page._add_source("/some/folder")  # normalized duplicate -> ignored
        assert len(page._sources) == 1
        assert "already in the list" in page._message.text

    def test_add_empty_ignored(self, db_page):
        _, _, page = page_and(db_page)
        page._add_source("")
        assert page._sources == []

    def test_remove_source(self, db_page):
        _, _, page = page_and(db_page)
        page._add_source("/a")
        norm = page._sources[0]
        page._on_remove(_evt(data=norm))
        assert page._sources == []

    def test_add_folder_picker(self, db_page, monkeypatch):
        _, _, page = page_and(db_page)
        monkeypatch.setattr(
            "videre.Dialog.select_directory", staticmethod(lambda: "/picked")
        )
        page._on_add_folder()
        assert len(page._sources) == 1 and "picked" in page._sources[0]

    def test_add_file_picker_filters_non_video(self, db_page, monkeypatch):
        _, _, page = page_and(db_page)
        monkeypatch.setattr(
            "videre.Dialog.select_many_files",
            staticmethod(lambda: ["/v.mp4", "/doc.txt"]),
        )
        page._on_add_file()
        assert len(page._sources) == 1  # only the video file
        assert "skipped" in page._message.text


class TestCreate:
    def test_create_empty_name(self, db_page):
        _, _, page = page_and(db_page)
        page._name_input.value = ""
        page._on_create()
        assert "enter a database name" in page._message.text

    def test_create_no_sources(self, db_page):
        _, _, page = page_and(db_page)
        page._name_input.value = "newdb"
        page._sources = []
        page._on_create()
        assert "add at least one source" in page._message.text

    def test_create_confirms_then_runs(self, db_page, monkeypatch):
        app, _, page = page_and(db_page)
        page._name_input.value = "newdb"
        page._add_source("/a")
        page._on_create()  # confirm fancybox
        calls = []
        monkeypatch.setattr(app, "run_process", lambda *a: calls.append(a))
        page._create("newdb", ["/a"])
        assert calls and calls[0][0] == "Creating 'newdb'" and page._sources == []


class TestDatabaseItemHover:
    """The item hover fix (kyuti databases_page.py:90-107): explicit hover/click,
    else videre's default gray Div hover would override the item's background."""

    def test_expanded_item_stays_blue_on_hover(self, db_page):
        _, _, page = page_and(db_page)
        page._expanded = "db2"
        header = _find(page._db_item("db2"), videre.Div)[0]
        # Expanded item keeps its blue on hover (the reported bug), not gray.
        assert header._style.default.background_color == theme.SELECTED_BG
        assert header._style.hover.background_color == theme.SELECTED_BG
        assert header._style.hover.background_color != videre.Colors.lightgray

    def test_collapsed_item_darkens_on_hover(self, db_page):
        _, _, page = page_and(db_page)
        page._expanded = None
        header = _find(page._db_item("db2"), videre.Div)[0]
        # Collapsed hover = #e8e8e8 (kyuti), NOT videre's default lightgray.
        assert header._style.hover.background_color == videre.parse_color("#e8e8e8")
        assert header._style.hover.background_color != videre.Colors.lightgray


def page_and(fixture):
    """Unpack the (app, window, page) fixture tuple."""
    return fixture
