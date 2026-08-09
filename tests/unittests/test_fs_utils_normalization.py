"""Mount-point normalization, including the Windows long-path (\\\\?\\) form.

AbsolutePath normalizes its mount point at construction, which is what makes
stored and scanned paths comparable. It must be idempotent and must not disturb
the long-path prefix: a path that stops resolving on disk, or that normalizes to
two different strings depending on how it was spelled, silently unindexes videos.
"""

import os

import pytest

from pysaurus.core import fs_utils
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.fs_utils import WIN_PREFIX, normalize_mount_point

windows_only = pytest.mark.skipif(
    os.name != "nt", reason="no drive prefix to normalize on POSIX"
)


@pytest.fixture
def long_path(tmp_path):
    """A real file whose path exceeds MAX_PATH, so AbsolutePath prefixes it."""
    deep = tmp_path.joinpath(*["d" * 40] * 6)
    try:
        deep.mkdir(parents=True)
        target = deep / "Mixed Case Name.mkv"
        with open(WIN_PREFIX + str(target), "wb") as file:
            file.write(b"x")
    except OSError:
        pytest.skip("long paths not usable here")
    assert len(str(target)) >= 260, "fixture must cross the MAX_PATH threshold"
    return str(target)


class TestNormalizeMountPoint:
    @windows_only
    def test_folds_the_drive_only(self):
        assert normalize_mount_point("c:\\Videos\\A Film.mkv") == (
            "C:\\Videos\\A Film.mkv"
        )

    def test_leaves_a_path_without_a_drive_alone(self):
        assert normalize_mount_point("/videos/Mixed Case.mkv") == (
            "/videos/Mixed Case.mkv"
        )

    @pytest.mark.parametrize("path", ["a:b.mkv", "C:\\Videos\\a.mkv", "/x/a:b.mkv"])
    def test_is_a_strict_no_op_off_windows(self, path, monkeypatch):
        """A colon is an ordinary filename character elsewhere.

        The shortcut keys on path[1] == ":", which on Linux matches the real
        file "a:b.mkv" and would rewrite its first letter.
        """
        monkeypatch.setattr(fs_utils.sys, "platform", "linux")
        assert normalize_mount_point(path) == path

    @windows_only
    @pytest.mark.parametrize(
        "path",
        [
            "C:\\Videos\\A Film.mkv",
            "\\\\?\\C:\\Videos\\A Film.mkv",
            "\\\\Server\\Share\\A Film.mkv",
            "\\\\?\\UNC\\Server\\Share\\A Film.mkv",
        ],
    )
    def test_is_idempotent_and_keeps_the_basename(self, path):
        once = normalize_mount_point(path)
        assert normalize_mount_point(once) == once
        assert os.path.basename(once) == os.path.basename(path)

    @windows_only
    @pytest.mark.parametrize(
        "path,expected",
        [
            ("c:\\Videos\\A Film.mkv", "C:\\Videos\\A Film.mkv"),
            ("\\\\?\\c:\\Videos\\A Film.mkv", "\\\\?\\C:\\Videos\\A Film.mkv"),
            ("\\\\Server\\Share\\A Film.mkv", "\\\\server\\share\\A Film.mkv"),
            (
                "\\\\?\\UNC\\Server\\Share\\A Film.mkv",
                "\\\\?\\UNC\\server\\share\\A Film.mkv",
            ),
            (
                "\\\\?\\unc\\Server\\Share\\A Film.mkv",
                "\\\\?\\UNC\\server\\share\\A Film.mkv",
            ),
        ],
    )
    def test_every_mount_point_shape_is_folded(self, path, expected):
        """Including behind the long-path prefix, where a shortcut could skip it.

        The UNC rows hold two constraints: server and share are folded, while
        the marker comes back as `\\\\?\\UNC\\` whatever case it arrived in --
        strip_win_prefix matches it literally.
        """
        assert normalize_mount_point(path) == expected

    @windows_only
    @pytest.mark.parametrize(
        "path", ["", "a", "C", ":", "\\\\?\\", "\\\\?\\C", "\\\\?\\C:", "rel\\x.mkv"]
    )
    def test_degenerate_inputs_do_not_raise(self, path):
        """The shortcuts index into the string; short inputs must not blow up."""
        assert normalize_mount_point(path) == normalize_mount_point(
            normalize_mount_point(path)
        )


class TestAbsolutePathNormalizesOnConstruction:
    @windows_only
    def test_short_path_gets_no_prefix(self):
        result = AbsolutePath("c:\\Videos\\A Film.mkv")
        assert result.path == "C:\\Videos\\A Film.mkv"
        # Re-parsing the stored form must land on the same value: ensure() would
        # hand the object straight back and prove nothing.
        assert AbsolutePath(result.path) == result

    @windows_only
    @pytest.mark.parametrize(
        "path,expected",
        [
            ("c:\\Videos\\A Film.mkv", "C:\\Videos\\A Film.mkv"),
            ("\\\\?\\c:\\Videos\\A Film.mkv", "\\\\?\\C:\\Videos\\A Film.mkv"),
            ("\\\\Server\\Share\\A Film.mkv", "\\\\server\\share\\A Film.mkv"),
            (
                "\\\\?\\UNC\\Server\\Share\\A Film.mkv",
                "\\\\?\\UNC\\server\\share\\A Film.mkv",
            ),
        ],
    )
    def test_construction_normalizes_every_shape(self, path, expected):
        """Guards the constructor, not just the helper it delegates to.

        A constructor that peels the long-path prefix off before normalizing
        leaves the UNC row untouched while the helper alone still looks right.
        """
        assert AbsolutePath(path).path == expected

    @windows_only
    @pytest.mark.parametrize("root", ["C:\\Videos", "\\\\Server\\Share"])
    @pytest.mark.parametrize("depth", [1, 6])
    def test_standard_path_gives_a_usable_path_back(self, root, depth):
        """standard_path must undo the prefix, not chop a fixed number of chars.

        A long UNC path is stored as `\\\\?\\UNC\\server\\share\\...`; slicing four
        characters off that yields `UNC\\server\\...`, which looks relative and
        reaches nothing. It feeds display, __fspath__, uri, and the PathTree
        that decides `discarded`, so it has to round-trip.
        """
        raw = root + "\\" + "\\".join(["d" * 40] * depth) + "\\film.mkv"
        result = AbsolutePath(raw)
        assert (len(raw) >= 260) == result.path.startswith(WIN_PREFIX)
        assert result.standard_path.lower() == raw.lower()
        assert result.standard_path.startswith(("C:\\", "\\\\"))

    @windows_only
    def test_long_path_keeps_a_single_prefix(self, long_path):
        result = AbsolutePath.ensure(long_path)
        assert result.path.startswith(WIN_PREFIX)
        assert not result.path[len(WIN_PREFIX) :].startswith(WIN_PREFIX)

    @windows_only
    def test_long_path_drive_is_normalized_inside_the_prefix(self, long_path):
        result = AbsolutePath.ensure(long_path).path
        drive = result[len(WIN_PREFIX) :][:2]
        assert drive == drive.upper()

    @windows_only
    def test_long_path_keeps_its_basename(self, long_path):
        assert os.path.basename(AbsolutePath.ensure(long_path).path) == (
            "Mixed Case Name.mkv"
        )

    @windows_only
    def test_long_path_still_resolves_on_disk(self, long_path):
        """The point of the prefix: normalizing must not break file access."""
        assert AbsolutePath.ensure(long_path).exists()

    @windows_only
    def test_long_path_is_idempotent(self, long_path):
        once = AbsolutePath(long_path)
        assert AbsolutePath(once.path) == once
        assert len(AbsolutePath(once.path).path) == len(once.path)

    @windows_only
    def test_both_drive_spellings_converge(self, long_path):
        swapped = long_path[0].swapcase() + long_path[1:]
        assert AbsolutePath.ensure(swapped) == AbsolutePath.ensure(long_path)
