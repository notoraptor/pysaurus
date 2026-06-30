"""Tests for videroid pages driven through a real VideroidApp + StepWindow.

Focus on behaviour that touches the model: the Videos page renders cards,
paginates, selects (incl. the point-7 'All covers the whole view' fix) and
deletes; Properties/Files pages reload without error and reflect the database.
"""

from pysaurus.interface.videroid.widgets.video_card import VideoCard
from tests.interface.videroid_interface._widget_tree import texts as _texts


def _videos_page(app):
    app.show_page("videos")
    return app._pages["videos"]


class TestVideosPageRendering:
    def test_reload_shows_cards(self, videroid_app):
        app, window = videroid_app
        page = _videos_page(app)
        window.render()
        cards = [c for c in page._cards.controls if isinstance(c, VideoCard)]
        assert len(cards) > 0
        assert len(cards) <= page.page_size

    def test_pagination_advances(self, videroid_app):
        app, _ = videroid_app
        page = _videos_page(app)
        page.page_size = 1
        page._reset_and_reload()
        if page._nb_pages() > 1:
            page._next(None)
            assert page._page_number == 1


class TestVideosPageSelection:
    def test_select_page_only_current_page(self, videroid_app):
        app, _ = videroid_app
        page = _videos_page(app)
        page.page_size = 1
        page._reset_and_reload()
        if app.context.get_videos(1000, 0).view_count > 1:
            page._select_page(None)
            assert len(page._selected_ids()) == 1  # only the single card shown

    def test_select_all_covers_whole_view(self, videroid_app):
        """Point-7 fix: 'All' enumerates every page, not just the current one."""
        app, _ = videroid_app
        page = _videos_page(app)
        page.page_size = 1
        page._reset_and_reload()
        all_ids = set(app.context.get_all_view_ids())
        page._select_all_in_view(None)
        assert page._selected_ids() == all_ids
        if len(all_ids) > 1:
            assert len(page._selected_ids()) > page.page_size

    def test_clear_selection(self, videroid_app):
        app, _ = videroid_app
        page = _videos_page(app)
        page._select_all_in_view(None)
        page._clear_selection()
        assert page._selected_ids() == set()


class TestVideosPageActions:
    def test_delete_selected_removes_from_db(self, videroid_app):
        app, _ = videroid_app
        page = _videos_page(app)
        before = app.context.get_videos(1000, 0).view_count
        page.page_size = 1
        page._reset_and_reload()
        page._select_page(None)
        ids = page._selected_ids()
        page._do_delete_selected(ids)
        after = app.context.get_videos(1000, 0).view_count
        assert after == before - len(ids)

    def test_video_toggle_watched_flips_flag(self, videroid_app):
        app, _ = videroid_app
        page = _videos_page(app)
        video = next(v for v in app.context.get_videos(1000, 0).result if v.readable)
        before = video.watched
        page.video_toggle_watched(video)  # toggle_watched + reload
        after = next(
            v
            for v in app.context.get_videos(1000, 0).result
            if v.video_id == video.video_id
        )
        assert after.watched != before  # the watched flag really flipped


class TestPropertiesPage:
    def test_table_reflects_database(self, videroid_app):
        app, window = videroid_app
        app.show_page("properties")
        window.render()
        page = app._pages["properties"]
        # header row + at least the "category" property row
        assert len(page._table.controls) >= 2
        assert "category" in _texts(page._table)  # the known property is listed


class TestFilesPage:
    def test_initial_scan_prompt(self, videroid_app):
        app, window = videroid_app
        app.show_page("files")
        window.render()
        page = app._pages["files"]
        # no scan yet -> the empty state is shown (a single holder control)
        assert page._holder.control is not None
        assert page._result is None
