"""
Tests for DatabaseOperations.set_folders validation against app_dir.

When a database knows its application directory, it must refuse any source
folder located inside (or equal to) that directory, to avoid indexing
Pysaurus internal files as video sources.
"""

import pytest

from pysaurus.application.application import Application
from pysaurus.application.exceptions import ForbiddenSourceFolder
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.database.saurus.pysaurus_collection import PysaurusCollection


@pytest.fixture
def app(tmp_path):
    return Application(home_dir=str(tmp_path))


@pytest.fixture
def db(app):
    return app.new_database("mydb", [])


class TestSetFoldersGuard:
    def test_external_folder_is_accepted(self, db, tmp_path):
        external = AbsolutePath.ensure(str(tmp_path / "external"))
        external.mkdir()
        db.ops.set_folders([external])
        assert set(db.get_folders()) == {external}

    def test_folder_inside_app_dir_is_rejected(self, app, db):
        sneaky = app.app_dir / "sneaky"
        sneaky.mkdir()
        with pytest.raises(ForbiddenSourceFolder):
            db.ops.set_folders([sneaky])

    def test_folder_equal_to_app_dir_is_rejected(self, app, db):
        with pytest.raises(ForbiddenSourceFolder):
            db.ops.set_folders([app.app_dir])

    def test_nested_folder_inside_app_dir_is_rejected(self, app, db):
        nested = app.app_dir / "a" / "b" / "c"
        nested.mkdir()
        with pytest.raises(ForbiddenSourceFolder):
            db.ops.set_folders([nested])

    def test_rejection_does_not_mutate_state(self, app, db, tmp_path):
        external = AbsolutePath.ensure(str(tmp_path / "external"))
        external.mkdir()
        db.ops.set_folders([external])
        before = sorted(db.get_folders())

        sneaky = app.app_dir / "sneaky"
        sneaky.mkdir()
        with pytest.raises(ForbiddenSourceFolder):
            db.ops.set_folders([external, sneaky])

        assert sorted(db.get_folders()) == before

    def test_sibling_of_app_dir_is_accepted(self, app, db, tmp_path):
        # A folder whose name shares a prefix with app_dir (e.g. ".Pysaurus2")
        # must not be confused with app_dir itself.
        similar = AbsolutePath.ensure(str(tmp_path / (app.app_dir.title + "2")))
        similar.mkdir()
        db.ops.set_folders([similar])
        assert set(db.get_folders()) == {similar}

    def test_parent_of_app_dir_is_accepted(self, app, db):
        # home_dir contains app_dir but is not itself under app_dir.
        # (Not a typical usage, but the guard should only forbid what is
        # strictly inside app_dir.)
        db.ops.set_folders([app.home_dir])
        assert set(db.get_folders()) == {app.home_dir}


class TestNoGuardWithoutAppDir:
    """A PysaurusCollection built directly (without app_dir) is not constrained."""

    def test_direct_instantiation_has_no_guard(self, tmp_path):
        db_folder = tmp_path / "standalone_db"
        db_folder.mkdir()
        db = PysaurusCollection(str(db_folder))
        # No app_dir means no validation, any folder is accepted.
        target = AbsolutePath.ensure(str(tmp_path / "any_folder"))
        target.mkdir()
        db.ops.set_folders([target])
        assert set(db.get_folders()) == {target}
