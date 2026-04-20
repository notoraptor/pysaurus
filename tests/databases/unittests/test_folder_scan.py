"""
Tests for FolderScanner (collect non-video file stats for DB folders).
"""

import os

import pytest

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.job_notifications import AbstractNotifier
from pysaurus.database.algorithms.folder_scan import (
    EMPTY_FOLDER_EXT,
    FolderScanProgress,
    FolderScanResult,
    FolderScanner,
)


class CapturingNotifier(AbstractNotifier):
    __slots__ = ("notifications",)

    def __init__(self):
        self.notifications: list = []

    def notify(self, notification) -> None:
        self.notifications.append(notification)


@pytest.fixture
def tree(tmp_path):
    """Sample tree: 3 videos (1 indexed, 2 unknown) + 3 junk files."""
    root = tmp_path / "videos"
    root.mkdir()
    (root / "v1.mp4").write_bytes(b"x" * 100)
    (root / "v2.mkv").write_bytes(b"x" * 200)
    (root / "thumb.jpg").write_bytes(b"x" * 10)
    sub = root / "sub"
    sub.mkdir()
    (sub / "v3.avi").write_bytes(b"x" * 300)
    (sub / "info.nfo").write_bytes(b"x" * 20)
    (sub / "download.part").write_bytes(b"x" * 5000)
    return root


class TestFolderScanner:
    def test_classifies_indexed_unknown_and_others(self, tree):
        indexed = {AbsolutePath.ensure(str(tree / "v1.mp4"))}
        scanner = FolderScanner([AbsolutePath.ensure(str(tree))], indexed)
        result = scanner.scan()

        assert set(result.videos_indexed) == {"mp4"}
        assert {f.path for f in result.videos_indexed["mp4"]} == indexed

        assert set(result.videos_unknown) == {"mkv", "avi"}
        assert {f.path for f in result.videos_unknown["mkv"]} == {
            AbsolutePath.ensure(str(tree / "v2.mkv"))
        }
        assert {f.path for f in result.videos_unknown["avi"]} == {
            AbsolutePath.ensure(str(tree / "sub" / "v3.avi"))
        }

        assert set(result.others) == {"jpg", "nfo", "part"}

    def test_records_file_size(self, tree):
        scanner = FolderScanner([AbsolutePath.ensure(str(tree))])
        result = scanner.scan()
        (jpg,) = result.others["jpg"]
        assert jpg.size == 10
        (part,) = result.others["part"]
        assert part.size == 5000

    def test_extension_is_lowercase(self, tmp_path):
        root = tmp_path / "case"
        root.mkdir()
        (root / "MIXED.JPG").write_bytes(b"x")
        (root / "shout.MP4").write_bytes(b"x")
        scanner = FolderScanner([AbsolutePath.ensure(str(root))])
        result = scanner.scan()
        assert "jpg" in result.others
        assert "mp4" in result.videos_unknown

    def test_file_without_extension_uses_empty_string(self, tmp_path):
        root = tmp_path / "noext"
        root.mkdir()
        (root / "README").write_bytes(b"x")
        scanner = FolderScanner([AbsolutePath.ensure(str(root))])
        result = scanner.scan()
        assert "" in result.others

    def test_empty_indexed_puts_all_videos_in_unknown(self, tree):
        scanner = FolderScanner([AbsolutePath.ensure(str(tree))])
        result = scanner.scan()
        assert not result.videos_indexed
        assert set(result.videos_unknown) == {"mp4", "mkv", "avi"}

    def test_nonexistent_folder_yields_empty_result(self, tmp_path):
        missing = AbsolutePath.ensure(str(tmp_path / "nope"))
        scanner = FolderScanner([missing])
        assert scanner.scan() == FolderScanResult()

    def test_empty_folder_is_reported_as_empty_folder(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        scanner = FolderScanner([AbsolutePath.ensure(str(empty))])
        result = scanner.scan()
        # An empty source folder is surfaced under the special
        # EMPTY_FOLDER_EXT pseudo-extension; nothing else is produced.
        assert result.videos_indexed == {} and result.videos_unknown == {}
        assert list(result.others) == [EMPTY_FOLDER_EXT]
        assert [i.path for i in result.others[EMPTY_FOLDER_EXT]] == [
            AbsolutePath.ensure(str(empty))
        ]

    def test_multiple_source_folders_are_merged(self, tmp_path):
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.mkdir()
        b.mkdir()
        (a / "one.jpg").write_bytes(b"x")
        (b / "two.jpg").write_bytes(b"x")
        scanner = FolderScanner(
            [AbsolutePath.ensure(str(a)), AbsolutePath.ensure(str(b))]
        )
        result = scanner.scan()
        assert len(result.others["jpg"]) == 2

    def test_does_not_follow_directory_symlinks(self, tmp_path):
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "reached.jpg").write_bytes(b"x")
        scanned = tmp_path / "scanned"
        scanned.mkdir()
        try:
            os.symlink(
                str(outside), str(scanned / "link_to_outside"), target_is_directory=True
            )
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation not permitted here")
        scanner = FolderScanner([AbsolutePath.ensure(str(scanned))])
        result = scanner.scan()
        # The symlinked directory must not be walked into.
        assert not result.others
        assert not result.videos_unknown
        assert not result.videos_indexed


class TestProgressNotifications:
    def test_emits_final_progress(self, tree):
        notifier = CapturingNotifier()
        scanner = FolderScanner([AbsolutePath.ensure(str(tree))], notifier=notifier)
        scanner.scan()
        progress = [
            n for n in notifier.notifications if isinstance(n, FolderScanProgress)
        ]
        assert progress, "expected at least one progress notification"
        last = progress[-1]
        # Everything discovered has been processed.
        assert last.folders_done == last.folders_discovered
        # 6 files were created in the fixture.
        assert last.files_found == 6

    def test_no_notification_when_all_folders_missing(self, tmp_path):
        notifier = CapturingNotifier()
        scanner = FolderScanner(
            [AbsolutePath.ensure(str(tmp_path / "ghost"))], notifier=notifier
        )
        scanner.scan()
        # Early return: no progress events emitted.
        assert not [
            n for n in notifier.notifications if isinstance(n, FolderScanProgress)
        ]


class TestEmptyFolders:
    def test_empty_subdirectory_is_reported(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        (root / "keep.jpg").write_bytes(b"x")
        (root / "empty_sub").mkdir()
        scanner = FolderScanner([AbsolutePath.ensure(str(root))])
        result = scanner.scan()
        assert EMPTY_FOLDER_EXT in result.others
        (info,) = result.others[EMPTY_FOLDER_EXT]
        assert info.path == AbsolutePath.ensure(str(root / "empty_sub"))
        assert info.size == 0

    def test_empty_root_is_reported(self, tmp_path):
        root = tmp_path / "nothing"
        root.mkdir()
        scanner = FolderScanner([AbsolutePath.ensure(str(root))])
        result = scanner.scan()
        assert EMPTY_FOLDER_EXT in result.others
        (info,) = result.others[EMPTY_FOLDER_EXT]
        assert info.path == AbsolutePath.ensure(str(root))

    def test_folder_with_only_subdirs_is_not_empty(self, tmp_path):
        root = tmp_path / "parent"
        root.mkdir()
        (root / "child").mkdir()
        (root / "child" / "leaf.txt").write_bytes(b"x")
        scanner = FolderScanner([AbsolutePath.ensure(str(root))])
        result = scanner.scan()
        # `root` has a subdir so it is not empty. `child` has `leaf.txt`, also
        # not empty. So no empty folder is recorded.
        assert EMPTY_FOLDER_EXT not in result.others

    def test_empty_folder_is_not_confused_with_video_or_indexed(self, tmp_path):
        root = tmp_path / "root"
        root.mkdir()
        (root / "empty").mkdir()
        scanner = FolderScanner([AbsolutePath.ensure(str(root))])
        result = scanner.scan()
        assert EMPTY_FOLDER_EXT in result.others
        assert not result.videos_indexed
        assert not result.videos_unknown


class TestGroupByMount:
    def test_single_mount(self, tmp_path):
        groups = FolderScanner._group_by_mount([AbsolutePath.ensure(str(tmp_path))])
        assert len(groups) == 1


class TestDatabaseAlgorithmsIntegration:
    def test_scan_folders_via_db_algos(self, tmp_path):
        from pysaurus.application.application import Application

        app = Application(home_dir=str(tmp_path))
        db = app.new_database("mydb", [])
        tree = tmp_path / "videos"
        tree.mkdir()
        (tree / "movie.mp4").write_bytes(b"x" * 10)
        (tree / "poster.jpg").write_bytes(b"x" * 5)

        db.ops.set_folders([AbsolutePath.ensure(str(tree))])
        result = db.algos.scan_folders()

        # DB is empty, so every video is unknown.
        assert set(result.videos_unknown) == {"mp4"}
        assert set(result.others) == {"jpg"}
        assert not result.videos_indexed
