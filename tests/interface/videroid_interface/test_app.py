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
        assert [label for label, _ in app._menu_database()] == [
            "Update Database",
            "Rename Database…",
            "Edit Folders…",
            "Close Database",
            "Quit",
        ]
        assert [label for label, _ in app._menu_view()] == ["Refresh View"]
        assert [label for label, _ in app._menu_help()] == ["About"]
        options = [label for label, _ in app._menu_options()]
        assert any("Page size" in label for label in options)
        assert any("Confirm deletion" in label for label in options)

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
