"""
Tests for FolderScanner (shared scan engine: files page + database update).
"""

import os

import pytest

from pysaurus.application.application import Application
from pysaurus.core import notifications
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.fs_utils import normalize_mount_point
from pysaurus.core.job_notifications import AbstractNotifier
from pysaurus.database.algorithms.folder_scan import (
    EMPTY_FOLDER_EXT,
    FolderScanner,
    FolderScanProgress,
    FolderScanResult,
)
from pysaurus.database.algorithms.videos import Videos


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

    @pytest.mark.skipif(
        os.name != "nt", reason="a POSIX mount point has no trailing separator"
    )
    def test_mount_point_ends_with_separator(self, tmp_path):
        (key,) = FolderScanner._group_by_mount([AbsolutePath.ensure(str(tmp_path))])
        assert key.endswith(os.sep)

    @pytest.mark.skipif(os.name != "nt", reason="Windows-only drive spelling")
    def test_drive_spelling_does_not_split_a_mount(self, tmp_path):
        """Two spellings of one drive must not become two threads / two disks.

        Handled by normalizing the seeds, so _group_by_mount itself never has
        to know about case.
        """
        a, b = tmp_path / "a", tmp_path / "b"
        a.mkdir()
        b.mkdir()
        swapped = str(a)[0].swapcase() + str(a)[1:]
        scanner = FolderScanner([swapped, str(b)])
        assert len(FolderScanner._group_by_mount(scanner.folders)) == 1

    @pytest.mark.skipif(os.name != "nt", reason="splitdrive finds no drive on POSIX")
    def test_fallback_key_keeps_the_mount_point_format(self, tmp_path, monkeypatch):
        """An unavailable volume must not yield a driver_id of another shape."""
        monkeypatch.setattr(
            AbsolutePath,
            "get_mount_point",
            lambda self: (_ for _ in ()).throw(OSError("volume unavailable")),
        )
        folder = AbsolutePath.ensure(str(tmp_path))
        (key,) = FolderScanner._group_by_mount([folder])
        assert key == os.path.splitdrive(folder.standard_path)[0] + os.sep
        assert key.endswith(os.sep)


class TestSeedNormalization:
    @pytest.mark.skipif(os.name != "nt", reason="Windows-only drive spelling")
    def test_scanned_paths_carry_a_normalized_mount_point(self, tree):
        """However the source is spelled, the walk yields comparable paths.

        This is what lets the database (migration m0006) and the scan meet
        without either side folding case at comparison time.
        """
        swapped = str(tree)[0].swapcase() + str(tree)[1:]
        result = FolderScanner([swapped]).scan()
        (info,) = result.videos_unknown["mp4"]
        assert info.path == AbsolutePath.ensure(str(tree / "v1.mp4"))
        assert info.driver_id == normalize_mount_point(info.driver_id)

    @pytest.mark.skipif(os.name != "nt", reason="Windows-only drive spelling")
    def test_indexed_matches_a_normalized_database(self, tree):
        db_paths = [AbsolutePath.ensure(str(tree / "v1.mp4"))]
        swapped = str(tree)[0].swapcase() + str(tree)[1:]
        result = FolderScanner([swapped], db_paths).scan()
        assert [f.path.title for f in result.videos_indexed["mp4"]] == ["v1"]
        assert "mp4" not in result.videos_unknown

    def test_unrelated_file_stays_unknown(self, tree):
        scanner = FolderScanner(
            [AbsolutePath.ensure(str(tree))],
            [AbsolutePath.ensure(str(tree / "zz.mp4"))],
        )
        result = scanner.scan()
        assert not result.videos_indexed
        assert [f.path.title for f in result.videos_unknown["mp4"]] == ["v1"]


class TestExtensionsFilter:
    def test_only_matching_extensions_collected(self, tree):
        scanner = FolderScanner(
            [AbsolutePath.ensure(str(tree))], extensions={"mp4", "avi"}
        )
        result = scanner.scan()
        assert set(result.videos_unknown) == {"mp4", "avi"}
        assert not result.videos_indexed
        # mkv filtered out, junk files (jpg, nfo, part) filtered out.
        assert not result.others

    def test_progress_counts_only_collected_files(self, tree):
        notifier = CapturingNotifier()
        scanner = FolderScanner(
            [AbsolutePath.ensure(str(tree))], notifier=notifier, extensions={"mp4"}
        )
        scanner.scan()
        progress = [
            n for n in notifier.notifications if isinstance(n, FolderScanProgress)
        ]
        assert progress[-1].files_found == 1

    def test_empty_folders_are_not_reported_under_a_filter(self, tmp_path):
        """A filter means "collect only these": empty folders are not one."""
        root = tmp_path / "root"
        (root / "empty").mkdir(parents=True)
        (root / "v.mp4").write_bytes(b"x")
        source = [AbsolutePath.ensure(str(root))]
        assert EMPTY_FOLDER_EXT in FolderScanner(source).scan().others
        filtered = FolderScanner(source, extensions={"mp4"}).scan()
        assert not filtered.others
        assert set(filtered.videos_unknown) == {"mp4"}


class TestFileSources:
    def test_video_file_source_is_collected(self, tree):
        target = AbsolutePath.ensure(str(tree / "v1.mp4"))
        scanner = FolderScanner([target])
        result = scanner.scan()
        (info,) = result.videos_unknown["mp4"]
        assert info.path == target
        assert info.size == 100
        assert info.mtime == os.path.getmtime(str(tree / "v1.mp4"))
        assert info.driver_id == target.get_mount_point()
        # A file source is never reported as an empty folder.
        assert EMPTY_FOLDER_EXT not in result.others

    def test_file_source_respects_extensions_filter(self, tree):
        target = AbsolutePath.ensure(str(tree / "thumb.jpg"))
        scanner = FolderScanner([target], extensions={"mp4"})
        assert scanner.scan() == FolderScanResult()


class TestRuntimeMetadata:
    def test_mtime_and_driver_id_recorded(self, tree):
        scanner = FolderScanner([AbsolutePath.ensure(str(tree))])
        result = scanner.scan()
        (info,) = result.videos_unknown["mp4"]
        assert info.mtime == os.path.getmtime(str(tree / "v1.mp4"))
        assert info.driver_id == AbsolutePath.ensure(str(tree)).get_mount_point()


class TestFollowLinks:
    def test_follow_links_walks_into_directory_symlinks(self, tmp_path):
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
        scanner = FolderScanner([AbsolutePath.ensure(str(scanned))], follow_links=True)
        result = scanner.scan()
        assert "jpg" in result.others
        assert {f.path.title for f in result.others["jpg"]} == {"reached"}

    def test_symlink_cycle_terminates(self, tmp_path):
        """A link pointing back at an ancestor must not loop forever."""
        root = tmp_path / "root"
        deep = root / "deep"
        deep.mkdir(parents=True)
        (deep / "inside.jpg").write_bytes(b"x")
        try:
            os.symlink(str(root), str(deep / "loop"), target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation not permitted here")
        scanner = FolderScanner([AbsolutePath.ensure(str(root))], follow_links=True)
        result = scanner.scan()
        # The cycle is cut, and the file behind it is still collected once.
        assert [f.path.title for f in result.others["jpg"]] == ["inside"]

    def test_two_paths_to_one_folder_are_both_collected(self, tmp_path):
        """A link to a sibling is not a cycle: both spellings must survive.

        Deduplicating on "have I seen this folder anywhere" drops one of them,
        and the update then flags every video indexed under the dropped
        spelling as not found.
        """
        root = tmp_path / "root"
        real = root / "real"
        real.mkdir(parents=True)
        (real / "movie.jpg").write_bytes(b"x")
        try:
            os.symlink(str(real), str(root / "link"), target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation not permitted here")
        result = FolderScanner(
            [AbsolutePath.ensure(str(root))], follow_links=True
        ).scan()
        assert sorted(f.path.standard_path for f in result.others["jpg"]) == sorted(
            [
                AbsolutePath.ensure(str(root / "link" / "movie.jpg")).standard_path,
                AbsolutePath.ensure(str(real / "movie.jpg")).standard_path,
            ]
        )

    def test_mutual_links_terminate(self, tmp_path):
        """Two folders pointing at each other loop without an ancestor link."""
        x, y = tmp_path / "x", tmp_path / "y"
        x.mkdir()
        y.mkdir()
        (x / "one.jpg").write_bytes(b"x")
        (y / "two.jpg").write_bytes(b"x")
        try:
            os.symlink(str(y), str(x / "to_y"), target_is_directory=True)
            os.symlink(str(x), str(y / "to_x"), target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("symlink creation not permitted here")
        result = FolderScanner([AbsolutePath.ensure(str(x))], follow_links=True).scan()
        # Terminates. x/to_y reaches two.jpg; x/to_y/to_x is x again, so it is
        # cut and one.jpg is not collected a second time under that spelling.
        assert sorted(f.path.standard_path for f in result.others["jpg"]) == sorted(
            [
                AbsolutePath.ensure(str(x / "one.jpg")).standard_path,
                AbsolutePath.ensure(str(x / "to_y" / "two.jpg")).standard_path,
            ]
        )

    def test_no_cycle_check_without_follow_links(self, tmp_path, monkeypatch):
        """The files page must not pay a stat() per directory."""
        root = tmp_path / "root"
        (root / "sub").mkdir(parents=True)

        def fail(*args, **kwargs):
            raise AssertionError("_identity must not run without follow_links")

        monkeypatch.setattr(FolderScanner, "_identity", staticmethod(fail))
        FolderScanner([AbsolutePath.ensure(str(root))]).scan()


class TestGetRuntimeInfoFromPaths:
    def test_collects_video_runtime_info(self, tree):
        notifier = CapturingNotifier()
        paths = Videos.get_runtime_info_from_paths(
            [AbsolutePath.ensure(str(tree))], notifier=notifier
        )
        expected = {
            AbsolutePath.ensure(str(tree / "v1.mp4")),
            AbsolutePath.ensure(str(tree / "v2.mkv")),
            AbsolutePath.ensure(str(tree / "sub" / "v3.avi")),
        }
        assert set(paths) == expected
        info = paths[AbsolutePath.ensure(str(tree / "v1.mp4"))]
        assert info.size == 100
        assert info.is_file
        assert info.driver_id == AbsolutePath.ensure(str(tree)).get_mount_point()
        assert any(
            isinstance(n, notifications.FinishedCollectingVideos)
            for n in notifier.notifications
        )

    def test_video_file_as_source(self, tree):
        """A source may be a direct video file path (legacy behavior)."""
        target = AbsolutePath.ensure(str(tree / "v1.mp4"))
        paths = Videos.get_runtime_info_from_paths(
            [target], notifier=CapturingNotifier()
        )
        assert set(paths) == {target}
        assert paths[target].size == 100


class TestDatabaseAlgorithmsIntegration:
    def test_scan_folders_via_db_algos(self, tmp_path):
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
