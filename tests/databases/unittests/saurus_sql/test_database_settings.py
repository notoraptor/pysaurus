"""Per-database settings live in the collection row and follow the property
they name."""

import pytest

from pysaurus.application import exceptions
from pysaurus.database.database_settings import DatabaseSettings
from pysaurus.database.saurus.pysaurus_collection import PysaurusCollection


@pytest.fixture
def db(mem_saurus_database) -> PysaurusCollection:
    return mem_saurus_database


def _target(db: PysaurusCollection, name: str) -> None:
    db.ops.set_settings(DatabaseSettings(generalize_title_property=name))


def test_defaults_are_empty(db):
    assert db.get_settings() == DatabaseSettings()


def test_round_trip_and_clear(db):
    db.prop_type_add("title_target", "str", "", False)
    _target(db, "title_target")
    assert db.get_settings().generalize_title_property == "title_target"
    db.ops.set_settings(DatabaseSettings())
    assert db.get_settings().generalize_title_property is None


def test_unknown_property_is_refused(db):
    with pytest.raises(exceptions.PropertyNotFound):
        _target(db, "nope")
    assert db.get_settings().generalize_title_property is None


@pytest.mark.parametrize("definition", [("int", 0, False), ("str", ["a", "b"], False)])
def test_only_a_non_enumerated_string_property_is_accepted(db, definition):
    prop_type, default, multiple = definition
    db.prop_type_add("bad", prop_type, default, multiple)
    with pytest.raises(exceptions.InvalidDatabaseSetting):
        _target(db, "bad")
    assert db.get_settings().generalize_title_property is None


def test_setting_follows_a_rename(db):
    db.prop_type_add("before", "str", "", False)
    _target(db, "before")
    db.prop_type_set_name("before", "after")
    assert db.get_settings().generalize_title_property == "after"


def test_setting_clears_when_the_property_is_deleted(db):
    db.prop_type_add("gone", "str", "", False)
    _target(db, "gone")
    db.prop_type_del("gone")
    assert db.get_settings().generalize_title_property is None
