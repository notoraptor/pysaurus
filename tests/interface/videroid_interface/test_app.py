"""Tests for the VideroidApp shell: navigation, title, menus, options.

Uses the `videroid_app` fixture (real VideroidApp on a headless StepWindow, with
an in-memory database injected and the Flask server / home scan patched out).
"""

import pytest


class TestNavigation:
    def test_starts_on_videos(self, videroid_app):
        app, _ = videroid_app
        assert app._current == "videos"

    def test_navigate_all_pages(self, videroid_app):
        app, window = videroid_app
        for name in ("databases", "videos", "properties", "files"):
            app.show_page(name)
            window.render()
            assert app._current == name

    def test_unknown_page_raises(self, videroid_app):
        app, _ = videroid_app
        with pytest.raises(ValueError):
            app.show_page("nope")

    def test_falls_back_to_databases_without_db(self, videroid_app):
        app, window = videroid_app
        app.context._api.database = None
        app.show_page("videos")  # needs a db -> falls back
        assert app._current == "databases"


class TestShell:
    def test_title_is_pysaurus_dash_db_on_videos(self, videroid_app):
        app, _ = videroid_app  # starts on the videos page, db open
        db = app.context.get_database_name()
        assert app._compute_title() == f"Pysaurus - {db}"  # videos-page format

    def test_menus_have_expected_actions(self, videroid_app):
        app, _ = videroid_app
        # With a database: full menu in kyuti order (Rename, Edit, Update, Close, Quit).
        assert [label for label, _ in app._menu_database(True)] == [
            "Rename Database…",
            "Edit Folders…",
            "Update Database",
            "Close Database",
            "Quit",
        ]
        # Without a database: only Quit stays reachable (kyuti keeps Quit active).
        assert [label for label, _ in app._menu_database(False)] == ["Quit"]
        assert [label for label, _ in app._menu_view()] == ["Refresh View"]
        assert [label for label, _ in app._menu_help()] == ["About"]
        options = [label for label, _ in app._menu_options()]
        assert any("Page size" in label for label in options)
        assert any("Confirm deletion" in label for label in options)

    def test_database_menu_stays_enabled_without_db(self, videroid_app, monkeypatch):
        # Quit must stay reachable with no DB, so the Database menu is not disabled.
        import videre

        from tests.interface.videroid_interface._widget_tree import find as _find

        app, _ = videroid_app
        monkeypatch.setattr(app.context, "has_database", lambda: False)
        app._refresh_shell()
        menus = _find(app._menu_holder.control, videre.ContextButton)
        db_menu = next(m for m in menus if m.text == "Database")
        assert not db_menu.disabled

    def test_page_size_option(self, videroid_app):
        app, _ = videroid_app
        app._set_page_size(50)
        assert app._pages["videos"].page_size == 50

    def test_toggle_confirm_deletion(self, videroid_app):
        app, _ = videroid_app
        videos = app._pages["videos"]
        before = videos.confirm_not_found_deletion
        app._toggle_confirm_del()
        assert videos.confirm_not_found_deletion is (not before)

    def test_set_status(self, videroid_app):
        app, _ = videroid_app
        app._set_status("Hello")
        assert app._status.text == "Hello"

    def test_status_bar_passive_and_clears_on_click(self, videroid_app):
        import videre

        from pysaurus.interface.videroid.app import _STATUS_STYLE
        from tests.interface.videroid_interface._widget_tree import find as _find

        app, _ = videroid_app
        # Passive look: default/hover/click share one background → no button flash.
        bgs = {
            _STATUS_STYLE[s]["background_color"] for s in ("default", "hover", "click")
        }
        assert bgs == {"#f0f0f0"}
        # Wired to clear the message on click (kyuti clearMessage → empty).
        app._set_status("hello")
        shell = app.window.controls[0]
        status_div = next(
            d for d in _find(shell, videre.Div) if app._status in _find(d, videre.Text)
        )
        status_div.click()  # mounted → runs on_click via call_now
        assert app._status.text == ""
