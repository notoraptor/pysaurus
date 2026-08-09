import os
import sys

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.fs_utils import normalize_mount_point


def test_absolute_path():
    """AbsolutePath is abspath, plus mount-point normalization."""
    wd = normalize_mount_point(os.path.abspath(".."))
    ap = AbsolutePath("..")
    assert wd == ap.standard_path

    sd = normalize_mount_point(os.path.abspath(__file__))
    sp = AbsolutePath(__file__)
    assert sd == sp.standard_path


def test_reuse_instance():
    path1 = AbsolutePath("..")
    path2 = AbsolutePath("..")
    assert path1 == path2
    assert path1 is not path2
    path3 = AbsolutePath.ensure(path1)
    assert path3 is path1
    path4 = AbsolutePath(str(path1))
    assert path1 == path4
    assert path1 is not path4


def test_join():
    path1 = AbsolutePath("a/b/c")
    path2 = AbsolutePath("a/b") / "c"
    path3 = AbsolutePath("a") / "b" / "c"
    assert path1 == path2
    assert path1 == path3


class TestGetMountPoint:
    def test_returns_string(self):
        ap = AbsolutePath(__file__)
        result = ap.get_mount_point()
        assert isinstance(result, str)

    def test_result_is_mount_point(self):
        ap = AbsolutePath(__file__)
        result = ap.get_mount_point()
        assert os.path.ismount(result)

    def test_result_is_ancestor_of_path(self):
        ap = AbsolutePath(__file__)
        result = ap.get_mount_point()
        # The mount point must be a prefix of the path
        standard = ap.standard_path
        assert standard.startswith(result) or standard.startswith(result.rstrip(os.sep))

    def test_current_directory(self):
        ap = AbsolutePath(".")
        result = ap.get_mount_point()
        assert os.path.ismount(result)

    def test_root_returns_root(self):
        if sys.platform == "win32":
            root = AbsolutePath("C:\\")
        else:
            root = AbsolutePath("/")
        result = root.get_mount_point()
        assert os.path.ismount(result)
        assert result == root.standard_path

    def test_nonexistent_path_returns_mount_point(self):
        """For a nonexistent path, walks up to the nearest real mount point."""
        if sys.platform == "win32":
            ap = AbsolutePath("C:\\nonexistent\\deep\\path\\file.txt")
        else:
            ap = AbsolutePath("/nonexistent/deep/path/file.txt")
        result = ap.get_mount_point()
        assert os.path.ismount(result)

    def test_windows_drive_root(self):
        if sys.platform != "win32":
            return
        ap = AbsolutePath("C:\\Users\\someone\\file.txt")
        result = ap.get_mount_point()
        assert os.path.ismount(result)
        # On a standard Windows install, C:\ is a mount point -- with an
        # uppercase drive, since AbsolutePath folds it at construction.
        assert result == "C:\\"

    def test_different_paths_same_disk_same_mount(self):
        """Two paths on the same disk return the same mount point."""
        ap1 = AbsolutePath(__file__)
        ap2 = AbsolutePath(os.path.dirname(__file__))
        assert ap1.get_mount_point() == ap2.get_mount_point()


class TestFileTitleAndExtension:
    def _basename(self, name: str) -> AbsolutePath:
        folder = "C:\\videos\\folder" if sys.platform == "win32" else "/videos/folder"
        return AbsolutePath(f"{folder}{os.sep}{name}")

    def test_classic_title_and_extension(self):
        ap = self._basename("video.mp4")
        assert ap.file_title == "video"
        assert ap.extension == "mp4"

    def test_extension_is_lowercased(self):
        ap = self._basename("VIDEO.MP4")
        assert ap.extension == "mp4"

    def test_no_dot_at_all(self):
        ap = self._basename("noext")
        assert ap.file_title == "noext"
        assert ap.extension == ""

    def test_multiple_extensions_split_on_last_dot(self):
        ap = self._basename("archive.tar.gz")
        assert ap.file_title == "archive.tar"
        assert ap.extension == "gz"

    def test_single_leading_dot_has_no_extension(self):
        ap = self._basename(".gitignore")
        assert ap.file_title == "gitignore"
        assert ap.extension == ""

    def test_multiple_leading_dots_have_no_extension(self):
        # A run of leading dots with nothing after but a dot-free remainder
        # is not an extension separator, regardless of how many dots.
        ap = self._basename("..backup")
        assert ap.file_title == "backup"
        assert ap.extension == ""

        ap = self._basename("...hidden")
        assert ap.file_title == "hidden"
        assert ap.extension == ""

    def test_leading_dots_with_a_later_dot_do_have_an_extension(self):
        # As soon as a second, non-leading dot appears, the leading dots no
        # longer protect the name: the last dot in the whole name wins.
        ap = self._basename(".a.b")
        assert ap.file_title == ".a"
        assert ap.extension == "b"

        ap = self._basename("..a...b")
        assert ap.file_title == "..a.."
        assert ap.extension == "b"
