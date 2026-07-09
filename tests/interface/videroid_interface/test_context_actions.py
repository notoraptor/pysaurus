"""Coverage of VideroidContext's action methods.

Most are thin delegations to the backend API (or to db.ops / db.algos). Driving
them against a real database would trigger threads (``@process``), VLC, the file
system or send2trash, so here `_api` is a Mock and we assert the delegation. The
few methods with real logic (trash_files, rename_database, drop_scanned_paths)
get dedicated tests.
"""

from unittest.mock import Mock

import pytest

from pysaurus.interface.videroid.context import VideroidContext, _VideroidAPI


@pytest.fixture
def mock_ctx():
    """A VideroidContext whose `_api` (and db/ops/algos) is a Mock."""
    ctx = object.__new__(VideroidContext)
    ctx._api = Mock()
    return ctx


class TestNotificationBridge:
    def test_api_property(self, mock_ctx):
        assert mock_ctx.api is mock_ctx._api

    def test_set_notification_sink(self, mock_ctx):
        sink = Mock()
        mock_ctx.set_notification_sink(sink)
        mock_ctx._api.set_sink.assert_called_once_with(sink)

    def test_videroid_api_notify_forwards_to_sink(self):
        api = object.__new__(_VideroidAPI)
        api._sink = None
        api._notify("ignored")  # no sink: no-op, no crash
        sink = Mock()
        api.set_sink(sink)
        api._notify("notif")
        sink.assert_called_once_with("notif")

    def test_set_exception_sink(self, mock_ctx):
        cb = Mock()
        mock_ctx.set_exception_sink(cb)
        mock_ctx._api.set_exception_callback.assert_called_once_with(cb)

    def test_run_thread_surfaces_exception(self):
        # A background @process op that raises must reach the exception callback
        # (else the failure is silent — the point of the robustness fix).
        api = object.__new__(_VideroidAPI)
        api._exception_callback = None
        caught = []
        api.set_exception_callback(caught.append)
        api._run_thread(lambda: 1 / 0).join()
        assert len(caught) == 1 and isinstance(caught[0], ZeroDivisionError)

    def test_run_thread_no_callback_is_silent(self):
        api = object.__new__(_VideroidAPI)
        api._exception_callback = None
        api._run_thread(lambda: 1 / 0).join()  # no callback -> swallowed, no crash


class TestDatabaseLifecycle:
    def test_get_database_names(self, mock_ctx):
        mock_ctx._api.application.get_database_names.return_value = ["a", "b"]
        assert mock_ctx.get_database_names() == ["a", "b"]

    def test_open_database(self, mock_ctx):
        mock_ctx.open_database("db", True)
        mock_ctx._api.open_database.assert_called_once_with("db", True)

    def test_create_database(self, mock_ctx):
        mock_ctx.create_database("db", ["/a"], False)
        mock_ctx._api.create_database.assert_called_once_with("db", ["/a"], False)

    def test_delete_database(self, mock_ctx):
        mock_ctx.delete_database("db")
        mock_ctx._api.application.delete_database_from_name.assert_called_once_with(
            "db"
        )

    def test_update_database(self, mock_ctx):
        mock_ctx.update_database()
        mock_ctx._api.update_database.assert_called_once_with()

    def test_close_database_delegates(self, mock_ctx):
        # The view reset itself is GuiAPI.close_database()'s responsibility
        # (it resets its own view internally) - context.py just delegates.
        mock_ctx.close_database()
        mock_ctx._api.close_database.assert_called_once_with()

    def test_close_app(self, mock_ctx):
        mock_ctx.close_app()
        mock_ctx._api.close_app.assert_called_once_with()

    def test_rename_database_updates_registry(self, mock_ctx):
        db = mock_ctx._api.database
        db.get_database_folder.side_effect = ["/old", "/new"]
        mock_ctx._api.application.databases = {"/old": db}
        mock_ctx.rename_database("NewName")
        db.rename.assert_called_once_with("NewName")
        assert mock_ctx._api.application.databases == {"/new": db}

    def test_rename_database_no_db(self, mock_ctx):
        mock_ctx._api.database = None
        mock_ctx._api.application.databases = {"/old": "kept"}
        assert mock_ctx.rename_database("X") is None  # guard: early return
        assert mock_ctx._api.application.databases == {"/old": "kept"}  # untouched

    def test_get_database_folders(self, mock_ctx):
        mock_ctx._api.database.get_folders.return_value = ["/a", "/b"]
        assert mock_ctx.get_database_folders() == ["/a", "/b"]

    def test_get_database_folders_no_db(self, mock_ctx):
        mock_ctx._api.database = None
        assert mock_ctx.get_database_folders() == []

    def test_set_database_folders(self, mock_ctx):
        mock_ctx.set_database_folders(["/a"])
        mock_ctx._api.database.ops.set_folders.assert_called_once_with(["/a"])


class TestViewFilters:
    def test_set_group(self, mock_ctx):
        mock_ctx.set_group(3)
        mock_ctx._api.set_group.assert_called_once_with(3)

    def test_classifier_select_group(self, mock_ctx):
        mock_ctx.classifier_select_group(2)
        mock_ctx._api.classifier_select_group.assert_called_once_with(2)

    def test_classifier_back(self, mock_ctx):
        mock_ctx.classifier_back()
        mock_ctx._api.classifier_back.assert_called_once_with()

    def test_classifier_reverse(self, mock_ctx):
        mock_ctx.classifier_reverse()
        mock_ctx._api.classifier_reverse.assert_called_once_with()

    def test_set_sources(self, mock_ctx):
        mock_ctx.set_sources([["readable"]])
        mock_ctx._api.set_sources.assert_called_once_with([["readable"]])

    # set_source_expression / get_source_expression now validate against the real
    # database (mirroring kyuti), so they are tested for real in
    # test_context.py::TestSourceExpression rather than against a mock.


class TestVideoActions:
    def test_open_video(self, mock_ctx):
        mock_ctx.open_video(7)
        mock_ctx._api.database.ops.open_video.assert_called_once_with(7)

    def test_open_containing_folder(self, mock_ctx):
        mock_ctx.open_containing_folder(7)
        mock_ctx._api.open_containing_folder.assert_called_once_with(7)

    def test_open_from_server(self, mock_ctx):
        mock_ctx._api.open_from_server.return_value = "vlc://x"
        assert mock_ctx.open_from_server(7) == "vlc://x"
        mock_ctx._api.open_from_server.assert_called_once_with(7)

    def test_open_random_video(self, mock_ctx):
        mock_ctx.open_random_video()
        mock_ctx._api.open_random_video.assert_called_once_with()

    def test_generate_playlist(self, mock_ctx):
        mock_ctx._api.playlist.return_value = "/tmp/p.xspf"
        assert mock_ctx.generate_playlist() == "/tmp/p.xspf"

    def test_classifier_concatenate_path(self, mock_ctx):
        mock_ctx.classifier_concatenate_path("tag")
        mock_ctx._api.classifier_concatenate_path.assert_called_once_with("tag")

    def test_find_similar_videos(self, mock_ctx):
        mock_ctx.find_similar_videos()
        mock_ctx._api.find_similar_videos.assert_called_once_with()

    def test_find_similar_videos_reencoded(self, mock_ctx):
        mock_ctx.find_similar_videos_reencoded()
        mock_ctx._api.find_similar_videos_reencoded.assert_called_once_with()

    def test_dismiss_similarity(self, mock_ctx):
        mock_ctx.dismiss_similarity(7, field="similarity_id_reencoded")
        mock_ctx._api.database.ops.set_similarities_from_list.assert_called_once_with(
            [7], [-1], field="similarity_id_reencoded"
        )

    def test_reset_similarity(self, mock_ctx):
        mock_ctx.reset_similarity(7)
        mock_ctx._api.database.ops.set_similarities_from_list.assert_called_once_with(
            [7], [None], field="similarity_id"
        )

    def test_move_video_file(self, mock_ctx):
        mock_ctx.move_video_file(7, "/dest")
        mock_ctx._api.move_video_file.assert_called_once_with(7, "/dest")

    def test_confirm_move(self, mock_ctx):
        mock_ctx.confirm_move(7, 9)
        mock_ctx._api.database.ops.move_video_entry.assert_called_once_with(7, 9)

    def test_confirm_unique_moves(self, mock_ctx):
        mock_ctx._api.database.algos.confirm_unique_moves.return_value = 3
        assert mock_ctx.confirm_unique_moves() == 3

    def test_confirm_unique_moves_no_db(self, mock_ctx):
        mock_ctx._api.database = None
        assert mock_ctx.confirm_unique_moves() == 0

    def test_get_database_folder_path(self, mock_ctx):
        mock_ctx._api.database.get_database_folder.return_value = "/dbs/mydb"
        assert mock_ctx.get_database_folder_path() == "/dbs/mydb"
        mock_ctx._api.database = None
        assert mock_ctx.get_database_folder_path() == ""

    def test_set_video_properties(self, mock_ctx):
        mock_ctx.set_video_properties(7, {"tag": ["x"], "old": []})
        mock_ctx._api.database.video_entry_set_tags.assert_called_once_with(
            7, {"tag": ["x"], "old": []}
        )

    def test_add_property_value_for_videos(self, mock_ctx):
        prop = Mock(multiple=True)
        mock_ctx._api.database.get_prop_types.return_value = [prop]
        mock_ctx.add_property_value_for_videos([1, 2], "tag", ["x"])
        mock_ctx._api.database.ops.set_property_for_videos.assert_called_once_with(
            "tag", {1: ["x"], 2: ["x"]}, merge=True
        )

    def test_rename_video(self, mock_ctx):
        mock_ctx.rename_video(7, "new")
        mock_ctx._api.database.ops.change_video_file_title.assert_called_once_with(
            7, "new"
        )

    def test_trash_video(self, mock_ctx):
        mock_ctx.trash_video(7)
        mock_ctx._api.database.ops.trash_video.assert_called_once_with(7)

    def test_delete_video_file(self, mock_ctx):
        mock_ctx.delete_video_file(7)
        mock_ctx._api.database.ops.delete_video.assert_called_once_with(7)

    def test_toggle_watched(self, mock_ctx):
        mock_ctx.toggle_watched(7)
        mock_ctx._api.database.ops.mark_as_read.assert_called_once_with(7)

    def test_toggle_watched_many(self, mock_ctx):
        mock_ctx.toggle_watched_many([1, 2])
        mock_ctx._api.database.ops.toggle_watched_many.assert_called_once_with([1, 2])

    def test_video_actions_no_db_are_noops(self, mock_ctx):
        mock_ctx._api.database = None
        mock_ctx.toggle_watched(1)
        mock_ctx.open_video(1)
        mock_ctx.rename_video(1, "x")
        mock_ctx.trash_video(1)
        mock_ctx.delete_video_file(1)
        mock_ctx.toggle_watched_many([1])
        mock_ctx.delete_video_entry(1)  # also no-op without db


class TestPropertyActions:
    def test_set_prop_type_multiple(self, mock_ctx):
        mock_ctx.set_prop_type_multiple("p", True)
        mock_ctx._api.database.prop_type_set_multiple.assert_called_once_with("p", True)

    def test_delete_property_values(self, mock_ctx):
        mock_ctx.delete_property_values("p", ["a"])
        mock_ctx._api.database.algos.delete_property_values.assert_called_once_with(
            "p", ["a"]
        )

    def test_replace_property_values(self, mock_ctx):
        mock_ctx._api.database.algos.replace_property_values.return_value = True
        assert mock_ctx.replace_property_values("p", ["a"], "b") is True

    def test_replace_property_values_no_db(self, mock_ctx):
        mock_ctx._api.database = None
        assert mock_ctx.replace_property_values("p", ["a"], "b") is False

    def test_move_property_values(self, mock_ctx):
        mock_ctx._api.database.algos.move_property_values.return_value = 5
        assert mock_ctx.move_property_values(["a"], "p", "q", concatenate=True) == 5

    def test_move_property_values_no_db(self, mock_ctx):
        mock_ctx._api.database = None
        assert mock_ctx.move_property_values(["a"], "p", "q", concatenate=False) == 0

    def test_fill_property_with_terms(self, mock_ctx):
        mock_ctx.fill_property_with_terms("p", only_empty=True)
        mock_ctx._api.database.algos.fill_property_with_terms.assert_called_once_with(
            "p", only_empty=True
        )

    def test_apply_on_prop_value(self, mock_ctx):
        mock_ctx.apply_on_prop_value("p", "lowercase")
        mock_ctx._api.database.ops.apply_on_prop_value.assert_called_once_with(
            "p", "lowercase"
        )


class TestScanAndTrash:
    def test_scan_folders(self, mock_ctx):
        mock_ctx.scan_folders()
        mock_ctx._api.scan_folders.assert_called_once_with()

    def test_get_last_scan_result(self, mock_ctx):
        mock_ctx._api.get_last_scan_result.return_value = "scan"
        assert mock_ctx.get_last_scan_result() == "scan"

    def test_trash_files_empty(self, mock_ctx):
        assert mock_ctx.trash_files([]) == (0, [])

    def test_trash_files_success(self, mock_ctx, monkeypatch):
        monkeypatch.setattr("send2trash.send2trash", lambda paths: None)
        monkeypatch.setattr("os.path.exists", lambda p: False)  # gone -> ok
        assert mock_ctx.trash_files(["/x"]) == (1, [])

    def test_trash_files_still_present_is_error(self, mock_ctx, monkeypatch):
        monkeypatch.setattr("send2trash.send2trash", lambda paths: None)
        monkeypatch.setattr("os.path.exists", lambda p: True)  # still there -> error
        ok, errors = mock_ctx.trash_files(["/x"])
        assert ok == 0 and len(errors) == 1

    def test_trash_files_oserror_swallowed(self, mock_ctx, monkeypatch):
        def raise_os(paths):
            raise OSError("io")

        monkeypatch.setattr("send2trash.send2trash", raise_os)
        monkeypatch.setattr("os.path.exists", lambda p: False)
        assert mock_ctx.trash_files(["/x"]) == (1, [])

    def test_trash_files_catastrophic_exception(self, mock_ctx, monkeypatch):
        def boom(paths):
            raise RuntimeError("nope")

        monkeypatch.setattr("send2trash.send2trash", boom)
        monkeypatch.setattr("os.path.exists", lambda p: True)
        ok, errors = mock_ctx.trash_files(["/x"])
        assert ok == 0 and "RuntimeError" in errors[0][1]


class TestDropScannedPaths:
    def test_filters_and_drops_empty_extension(self, mock_ctx):
        class _F:
            def __init__(self, p):
                self.path = p

        class _Result:
            def __init__(self):
                self.others = {"tmp": [_F("a"), _F("b")], "nfo": [_F("c")]}

        result = _Result()
        mock_ctx._api.get_last_scan_result.return_value = result
        mock_ctx.drop_scanned_paths({"a", "c"})
        assert [f.path for f in result.others["tmp"]] == ["b"]
        assert "nfo" not in result.others  # emptied -> removed
