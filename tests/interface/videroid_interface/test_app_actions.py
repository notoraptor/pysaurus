"""Coverage for VideroidApp menu actions, run_process and notification routing.

Backend mutations and the threaded ops are mocked; dialog handlers are invoked
directly (they set a fancybox on the real StepWindow)."""

from pysaurus.core.notifications import DatabaseReady, Message
from pysaurus.interface.videroid.dialogs.edit_folders_dialog import EditFoldersDialog
from tests.interface.videroid_interface._widget_tree import texts as _texts


def _evt(**attrs):
    return type("Evt", (), attrs)()


class _T:
    def __init__(self, value):
        self.value = value


class TestRunProcess:
    def test_run_process_then_finish(self, videroid_app):
        app, _ = videroid_app
        ended = []
        app.run_process("Task", lambda: None, ended.append)
        proc = app._active_process
        assert proc is not None
        end = DatabaseReady()
        proc.on_notification(end)  # End -> Continue button
        proc._on_continue(None)  # -> finished(end): clears process, calls on_end
        assert app._active_process is None
        assert ended == [end]


class TestNotificationRouting:
    def test_routes_to_current_page(self, videroid_app, monkeypatch):
        app, _ = videroid_app
        received = []
        monkeypatch.setattr(
            app._pages[app._current], "on_notification", received.append
        )
        msg = Message("x")
        app.on_notification(msg)  # no active process -> current page
        assert received == [msg]

    def test_routes_to_active_process(self, videroid_app):
        app, _ = videroid_app
        app.run_process("T", lambda: None, lambda e: None)
        app.on_notification(Message("y"))  # -> active process
        assert "y" in _texts(app._active_process._log)  # shown in the activity log


class TestNavigationAndTitle:
    def test_on_nav(self, videroid_app):
        app, window = videroid_app
        app._on_nav(_evt(data="properties"))
        window.render()
        assert app._current == "properties"

    def test_title_while_processing(self, videroid_app):
        app, _ = videroid_app
        app.run_process("Updating", lambda: None, lambda e: None)
        assert "Updating" in app._compute_title()

    def test_title_other_page(self, videroid_app):
        app, _ = videroid_app
        app.show_page("properties")
        db = app.context.get_database_name()
        assert app._compute_title() == f"Pysaurus - Properties - {db}"


class TestMenuActions:
    def test_update_db(self, videroid_app, monkeypatch):
        app, _ = videroid_app
        calls = []
        monkeypatch.setattr(app, "run_process", lambda *a: calls.append(a))
        app._update_db()
        assert calls and calls[0][0] == "Updating database"  # right process title

    def test_rename_db(self, videroid_app, monkeypatch):
        app, _ = videroid_app
        monkeypatch.setattr(app.context, "get_database_name", lambda: "old")
        renamed = []
        monkeypatch.setattr(app.context, "rename_database", renamed.append)
        app._rename_db()  # set_fancybox
        app._do_rename_db(_T("newname"))
        assert renamed == ["newname"]

    def test_edit_folders_applies_only_when_changed(self, videroid_app, monkeypatch):
        app, _ = videroid_app
        monkeypatch.setattr(app.context, "get_database_folders", lambda: ["/a"])
        app._edit_folders()  # set_fancybox
        applied = []
        monkeypatch.setattr(app.context, "set_database_folders", applied.append)
        app._do_edit_folders(EditFoldersDialog(["/a"]))  # unchanged -> no-op
        assert applied == []
        changed = EditFoldersDialog(["/a", "/b"])
        app._do_edit_folders(changed)  # changed -> applied
        assert applied == [changed.get_folders()]

    def test_close_db(self, videroid_app):
        app, _ = videroid_app
        assert app.context.has_database()
        app._close_db()  # confirm
        app._do_close_db()  # real close: nulls the db ref + navigates
        assert not app.context.has_database()
        assert app._current == "databases"

    def test_quit(self, videroid_app, monkeypatch):
        import pygame

        app, window = videroid_app
        closed = []
        monkeypatch.setattr(app.context, "close_app", lambda: closed.append(1))
        assert window.windowing.running  # loop is "running" by default
        app._quit()  # confirm
        app._do_quit()
        # App closed and the loop is asked to stop by CLEARING `running` — not by
        # calling stop()/pygame.quit() mid-step (which crashed the real app with
        # "video system not initialized"). run()'s finally does the pygame.quit().
        assert closed == [1]
        assert window.windowing.running is False
        # Regression guard: pygame must still be initialized (the old code called
        # windowing.stop() = pygame.quit() here, tearing it down mid-frame).
        assert pygame.display.get_init()

    def test_refresh_view(self, videroid_app):
        app, _ = videroid_app
        app._refresh_view()
        assert "refreshed" in app._status.text.lower()

    def test_about(self, videroid_app):
        app, window = videroid_app
        app._about()  # alert
        assert window.has_fancybox()  # an About dialog is actually shown


class TestRun:
    def test_run_returns_window_run(self, videroid_app, monkeypatch):
        app, _ = videroid_app
        monkeypatch.setattr(type(app.window), "run", lambda self: 0)
        monkeypatch.setattr(app.context, "close_app", lambda: None)
        assert app.run() == 0
