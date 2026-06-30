"""Coverage for the Files page: scan state, tabs, tables, trash, open folder.

A fake FolderScanResult is injected into the backend's _last_scan_result so the
"scanned" state renders without a real folder scan.
"""

import pytest

from tests.interface.videroid_interface._widget_tree import texts as _texts


def _evt(**attrs):
    return type("Evt", (), attrs)()


def _capture(monkeypatch, window, method):
    """Capture calls to a slotted Window method (confirm/alert).

    Window uses __slots__, so the method must be patched at the CLASS level
    (instance attributes are read-only). Returns a list of (args, kwargs).
    """
    calls = []
    monkeypatch.setattr(
        type(window), method, lambda self, *a, **k: calls.append((a, k))
    )
    return calls


class _FF:
    def __init__(self, path, size=10):
        self.path = path
        self.size = size


class _Scan:
    def __init__(self):
        self.others = {
            "tmp": [_FF("/d/a.tmp"), _FF("/d/b.tmp")],
            "nfo": [_FF("/d/c.nfo")],
        }
        self.videos_indexed = {"mp4": [_FF("/d/v.mp4", 1000)]}
        self.videos_unknown = {"avi": [_FF("/d/u.avi", 500)]}


@pytest.fixture
def scanned(videroid_app):
    app, window = videroid_app
    app.context._api._last_scan_result = _Scan()
    app.show_page("files")
    window.render()
    return app, window, app._pages["files"]


class TestFilesUtils:
    def test_human_size_units(self):
        from pysaurus.interface.videroid.pages.files_page import _human_size

        assert _human_size(0).endswith("B")
        assert "KB" in _human_size(2048)
        assert "TB" in _human_size(2**42)

    def test_ext_label(self):
        from pysaurus.database.algorithms.folder_scan import EMPTY_FOLDER_EXT
        from pysaurus.interface.videroid.pages.files_page import _ext_label

        assert _ext_label("") == "(no extension)"
        assert _ext_label("mp4") == "mp4"
        assert _ext_label(EMPTY_FOLDER_EXT) == "(empty folder)"


class TestFilesEmptyState:
    def test_empty_without_scan(self, videroid_app):
        app, window = videroid_app
        app.context._api._last_scan_result = None
        app.show_page("files")
        window.render()
        page = app._pages["files"]
        assert page._result is None

    def test_on_scan_runs_process(self, videroid_app, monkeypatch):
        app, _ = videroid_app
        calls = []
        monkeypatch.setattr(app, "run_process", lambda *a: calls.append(a))
        app._pages["files"]._on_scan(None)
        assert calls and calls[0][0] == "Scanning files"  # right process title
        app._pages["files"]._after_scan(None)  # navigates back to files
        assert app._current == "files"


class TestFilesScannedState:
    def test_scanned_renders_and_summary(self, scanned):
        _, _, page = scanned
        assert page._result is not None
        assert "other files" in page._summary.text

    def test_tab_switch_to_stats(self, scanned):
        _, window, page = scanned
        page._tabs._on_click(_evt(data=1))  # Video stats tab -> _stats_tab
        window.render()
        assert page._tabs.active_index == 1

    def test_select_extension(self, scanned):
        _, _, page = scanned
        page._select_ext(_evt(data="nfo"))
        assert page._sel_ext == "nfo"

    def test_file_check_toggles(self, scanned):
        _, _, page = scanned
        page._on_file_check(_evt(checked=True, data="/d/a.tmp"))
        assert "/d/a.tmp" in page._selected_files
        page._on_file_check(_evt(checked=False, data="/d/a.tmp"))
        assert "/d/a.tmp" not in page._selected_files

    def test_filter_then_refresh(self, scanned):
        _, window, page = scanned
        page._sel_ext = "tmp"
        page._filter.value = "a.tmp"
        page._tabs.refresh()  # rebuilds the Others tab with the filter applied
        window.render()
        shown = _texts(page._tabs._holder.control)
        assert any("a.tmp" in t for t in shown)  # the matching file is listed
        assert not any("b.tmp" in t for t in shown)  # the non-matching one is hidden


class TestFilesTrash:
    def test_trash_selected_confirms_and_fires(self, scanned, monkeypatch):
        app, _, page = scanned
        monkeypatch.setattr(app.context, "trash_files", lambda paths: (len(paths), []))
        calls = _capture(monkeypatch, page.app.window, "confirm")
        page._selected_files = {"/d/a.tmp"}
        page._trash_selected(None)
        content, on_confirm = calls[0][0][0], calls[0][1]["on_confirm"]
        assert any("/d/a.tmp" in t for t in _texts(content))  # confirm lists the file
        on_confirm()  # confirming really trashes the selected path
        kept = [
            f.path for f in app.context._api._last_scan_result.others.get("tmp", [])
        ]
        assert "/d/a.tmp" not in kept

    def test_trash_all_lists_every_file(self, scanned, monkeypatch):
        _, _, page = scanned
        calls = _capture(monkeypatch, page.app.window, "confirm")
        page._trash_all(_evt(data="tmp"))  # all "tmp" files
        shown = _texts(calls[0][0][0])
        assert any("all 2 'tmp' file(s)" in t for t in shown)  # subject count
        assert any("/d/a.tmp" in t for t in shown)
        assert any("/d/b.tmp" in t for t in shown)

    def test_confirm_trash_bulk_warning(self, scanned, monkeypatch):
        _, _, page = scanned
        calls = _capture(monkeypatch, page.app.window, "confirm")
        page._confirm_trash([f"/d/{i}.tmp" for i in range(600)], "600 files")
        # >500 paths -> the irreversible-bulk warning is shown.
        assert any("Bulk operation" in t for t in _texts(calls[0][0][0]))

    def test_do_trash_drops_paths(self, scanned, monkeypatch):
        app, _, page = scanned
        monkeypatch.setattr(app.context, "trash_files", lambda paths: (len(paths), []))
        page._sel_ext = "tmp"
        page._do_trash(["/d/a.tmp", "/d/b.tmp"])
        # both tmp files gone -> the extension is removed; selection moves off "tmp"
        assert "tmp" not in app.context._api._last_scan_result.others
        assert page._sel_ext != "tmp"

    def test_do_trash_reports_errors_and_keeps_path(self, scanned, monkeypatch):
        app, _, page = scanned
        monkeypatch.setattr(
            app.context, "trash_files", lambda paths: (0, [(paths[0], "fail")])
        )
        alerts = _capture(monkeypatch, page.app.window, "alert")
        page._sel_ext = "tmp"
        page._do_trash(["/d/a.tmp"])  # the file failed to trash
        kept = [f.path for f in app.context._api._last_scan_result.others["tmp"]]
        assert "/d/a.tmp" in kept  # failed path is NOT dropped from the scan
        assert alerts and "failed" in alerts[0][0][0]  # an error alert is shown


class TestFilesOpenFolder:
    def test_open_folder_no_selection_alerts(self, scanned, monkeypatch):
        _, _, page = scanned
        alerts = _capture(monkeypatch, page.app.window, "alert")
        page._selected_files = set()
        page._open_folder(None)
        assert alerts and "Select at least one file" in alerts[0][0][0]

    def test_open_folder_opens_parent_on_windows(self, scanned, monkeypatch):
        import os
        import sys

        _, _, page = scanned
        page._selected_files = {"/d/a.tmp"}
        opened = []
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setattr(os, "startfile", opened.append, raising=False)
        page._open_folder(None)
        assert opened == ["/d"]  # opens the file's PARENT folder

    def test_open_folder_handles_error_with_alert(self, scanned, monkeypatch):
        import os
        import sys

        _, _, page = scanned
        page._selected_files = {"/d/a.tmp"}

        def boom(folder):
            raise RuntimeError("nope")

        alerts = _capture(monkeypatch, page.app.window, "alert")
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setattr(os, "startfile", boom, raising=False)
        page._open_folder(None)
        msg = alerts[0][0][0]
        assert "RuntimeError" in msg and "nope" in msg

    def test_open_folder_linux_uses_xdg_open(self, scanned, monkeypatch):
        import subprocess
        import sys

        _, _, page = scanned
        page._selected_files = {"/d/a.tmp"}
        calls = []
        monkeypatch.setattr(sys, "platform", "linux")
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: calls.append((a, k)))
        page._open_folder(None)
        assert calls and calls[0][0][0] == ["xdg-open", "/d"]

    def test_open_folder_darwin_uses_open(self, scanned, monkeypatch):
        import subprocess
        import sys

        _, _, page = scanned
        page._selected_files = {"/d/a.tmp"}
        calls = []
        monkeypatch.setattr(sys, "platform", "darwin")
        monkeypatch.setattr(subprocess, "run", lambda *a, **k: calls.append((a, k)))
        page._open_folder(None)
        assert calls and calls[0][0][0] == ["open", "/d"]
