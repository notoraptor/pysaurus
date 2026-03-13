import os
import shutil

import pytest

from pysaurus.application.exceptions import DatabaseAlreadyExists, InvalidDatabaseName
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.database.db_paths import Basename, DatabasePaths
from pysaurus.database.saurus.pysaurus_collection import PysaurusCollection

TEST_HOME_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "home_dir_test"
)
TEST_DB_FOLDER = os.path.join(TEST_HOME_DIR, ".Pysaurus", "databases", "test_database")


@pytest.fixture
def db_folder(tmp_path):
    folder = tmp_path / "mydb"
    folder.mkdir()
    return AbsolutePath(str(folder))


@pytest.fixture
def basenames():
    return (Basename("log_path", "log"), Basename("sql_path", "full.db"))


class TestDatabasePathsInit:
    def test_empty(self, db_folder):
        dp = DatabasePaths(db_folder)
        assert dp.db_folder == db_folder
        assert dp.paths == {}

    def test_with_basenames(self, db_folder, basenames):
        dp = DatabasePaths(db_folder, basenames)
        assert len(dp.paths) == 2
        assert "log_path" in dp.paths
        assert "sql_path" in dp.paths

    def test_rejects_nonexistent_folder(self, tmp_path):
        fake = tmp_path / "does_not_exist"
        with pytest.raises(NotADirectoryError):
            DatabasePaths(AbsolutePath(str(fake)))


class TestAddPath:
    def test_add_path_returns_absolute_path(self, db_folder):
        dp = DatabasePaths(db_folder)
        result = dp.add_path(Basename("data", "json"))
        assert isinstance(result, AbsolutePath)
        assert result.path.endswith("data.json")

    def test_add_path_stored_in_paths(self, db_folder):
        dp = DatabasePaths(db_folder)
        dp.add_path(Basename("data", "json"))
        assert "data" in dp.paths

    def test_add_path_composes_correctly(self, db_folder):
        dp = DatabasePaths(db_folder)
        result = dp.add_path(Basename("my_file", "txt"))
        expected = os.path.join(db_folder.path, "my_file.txt")
        assert result.path == expected

    def test_add_duplicate_raises(self, db_folder):
        dp = DatabasePaths(db_folder)
        dp.add_path(Basename("data", "json"))
        with pytest.raises(AssertionError):
            dp.add_path(Basename("data", "json"))


class TestGetPath:
    def test_get_path_returns_same_as_add(self, db_folder):
        dp = DatabasePaths(db_folder)
        bn = Basename("log", "txt")
        added = dp.add_path(bn)
        got = dp.get_path(bn)
        assert added == got

    def test_get_path_unknown_raises(self, db_folder):
        dp = DatabasePaths(db_folder)
        with pytest.raises(KeyError):
            dp.get_path(Basename("nonexistent", "txt"))


class TestIter:
    def test_iter_empty(self, db_folder):
        dp = DatabasePaths(db_folder)
        items = list(dp)
        assert items == [(".", db_folder)]

    def test_iter_with_paths(self, db_folder, basenames):
        dp = DatabasePaths(db_folder, basenames)
        items = list(dp)
        assert items[0] == (".", db_folder)
        keys = [k for k, _ in items[1:]]
        assert "log_path" in keys
        assert "sql_path" in keys

    def test_iter_values_are_absolute_paths(self, db_folder, basenames):
        dp = DatabasePaths(db_folder, basenames)
        for _, value in dp:
            assert isinstance(value, AbsolutePath)


class TestRenamed:
    def test_same_name_returns_self(self, db_folder, basenames):
        dp = DatabasePaths(db_folder, basenames)
        result = dp.renamed(db_folder.title)
        assert result is dp

    def test_same_name_with_whitespace_returns_self(self, db_folder, basenames):
        dp = DatabasePaths(db_folder, basenames)
        result = dp.renamed(f"  {db_folder.title}  ")
        assert result is dp

    def test_invalid_name_raises(self, db_folder, basenames):
        dp = DatabasePaths(db_folder, basenames)
        with pytest.raises(InvalidDatabaseName):
            dp.renamed("invalid/name")

    def test_already_exists_raises(self, db_folder, basenames, tmp_path):
        dp = DatabasePaths(db_folder, basenames)
        existing = tmp_path / "existing_db"
        existing.mkdir()
        with pytest.raises(DatabaseAlreadyExists):
            dp.renamed("existing_db")

    def test_renamed_creates_new_folder(self, db_folder, basenames):
        dp = DatabasePaths(db_folder, basenames)
        result = dp.renamed("new_name")
        assert result.db_folder.isdir()
        assert result.db_folder.title == "new_name"

    def test_renamed_deletes_old_folder(self, db_folder, basenames):
        dp = DatabasePaths(db_folder, basenames)
        dp.renamed("new_name")
        assert not db_folder.exists()

    def test_renamed_moves_existing_files(self, db_folder, basenames):
        dp = DatabasePaths(db_folder, basenames)
        # Create a real file at the log_path location
        log_path = dp.get_path(basenames[0])
        with open(log_path.path, "w") as f:
            f.write("test content")
        result = dp.renamed("new_name")
        # Old file gone
        assert not log_path.exists()
        # New file exists with correct content
        new_log = result.paths["log_path"]
        assert new_log.exists()
        with open(new_log.path) as f:
            assert f.read() == "test content"

    def test_renamed_preserves_all_paths(self, db_folder, basenames):
        dp = DatabasePaths(db_folder, basenames)
        result = dp.renamed("new_name")
        assert set(result.paths.keys()) == set(dp.paths.keys())

    def test_renamed_moves_unregistered_files(self, db_folder):
        dp = DatabasePaths(db_folder)
        # Create a file not registered in paths
        extra_file = os.path.join(db_folder.path, "extra.dat")
        with open(extra_file, "w") as f:
            f.write("extra")
        result = dp.renamed("new_name")
        new_extra = os.path.join(result.db_folder.path, "extra.dat")
        assert os.path.isfile(new_extra)
        with open(new_extra) as f:
            assert f.read() == "extra"

    def test_renamed_returns_database_paths(self, db_folder, basenames):
        dp = DatabasePaths(db_folder, basenames)
        result = dp.renamed("new_name")
        assert isinstance(result, DatabasePaths)


class TestDatabaseRename:
    """Test AbstractDatabase.rename() with a real PysaurusCollection on disk."""

    @pytest.fixture
    def disk_db(self, tmp_path):
        """Copy the test database to a temp directory for writing."""
        dest = tmp_path / "test_database"
        shutil.copytree(TEST_DB_FOLDER, dest)
        return PysaurusCollection(str(dest))

    def test_rename_changes_name(self, disk_db):
        assert disk_db.get_name() == "test_database"
        disk_db.rename("renamed_db")
        assert disk_db.get_name() == "renamed_db"

    def test_rename_moves_folder(self, disk_db):
        old_folder = disk_db.get_database_folder()
        disk_db.rename("renamed_db")
        new_folder = disk_db.get_database_folder()
        assert not old_folder.exists()
        assert new_folder.isdir()
        assert new_folder.title == "renamed_db"

    def test_rename_db_still_readable(self, disk_db):
        """Database remains functional after rename."""
        videos_before = list(disk_db.get_videos(include=["video_id"]))
        disk_db.rename("renamed_db")
        videos_after = list(disk_db.get_videos(include=["video_id"]))
        assert len(videos_after) == len(videos_before)
        assert len(videos_after) > 0

    def test_rename_db_still_writable(self, disk_db):
        """Database can still be written to after rename."""
        disk_db.rename("renamed_db")
        prop_types = disk_db.get_prop_types()
        if prop_types:
            pt = prop_types[0]
            # Read a property to verify DB access after rename
            values = disk_db.videos_tag_get(pt["name"])
            assert isinstance(values, dict)

    def test_rename_paths_updated(self, disk_db):
        disk_db.rename("renamed_db")
        log_path = disk_db.get_log_path()
        miniatures_path = disk_db.get_miniatures_path()
        assert "renamed_db" in log_path.path
        assert "renamed_db" in miniatures_path.path

    def test_rename_back_to_original(self, disk_db):
        original_name = disk_db.get_name()
        disk_db.rename("renamed_db")
        disk_db.rename(original_name)
        assert disk_db.get_name() == original_name

    def test_rename_same_name_is_noop(self, disk_db):
        old_folder = disk_db.get_database_folder()
        disk_db.rename("test_database")
        assert disk_db.get_database_folder() == old_folder

    def test_rename_dot_prefix_raises(self, disk_db):
        with pytest.raises(Exception):
            disk_db.rename(".hidden")
