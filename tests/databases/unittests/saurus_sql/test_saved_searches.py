"""Saved searches are keyed by their expression; the name is a unique label."""

import pytest

from pysaurus.application import exceptions
from pysaurus.database.saurus.pysaurus_collection import PysaurusCollection
from pysaurus.database.saved_search import SavedSearch


@pytest.fixture
def db(mem_saurus_database) -> PysaurusCollection:
    return mem_saurus_database


def test_starts_empty(db):
    assert db.get_saved_searches() == []


def test_round_trip(db):
    saved = db.ops.save_search("width > 100", "wide")
    assert saved == SavedSearch(expression="width > 100", name="wide")
    assert db.get_saved_searches() == [saved]


def test_resaving_an_expression_renames_it(db):
    db.ops.save_search("width > 100", "wide")
    db.ops.save_search("  width > 100 ", "large")
    assert db.get_saved_searches() == [SavedSearch("width > 100", "large")]


def test_blank_name_means_no_name(db):
    assert db.ops.save_search("width > 100", "  ").name is None
    assert db.ops.save_search("width > 100").name is None


def test_a_name_labels_one_expression(db):
    db.ops.save_search("width > 100", "wide")
    with pytest.raises(exceptions.InvalidSavedSearch):
        db.ops.save_search("height > 100", "wide")
    assert db.get_saved_searches() == [SavedSearch("width > 100", "wide")]


def test_invalid_expression_is_refused(db):
    with pytest.raises(exceptions.InvalidSourceExpression):
        db.ops.save_search("width >", "broken")
    assert db.get_saved_searches() == []


def test_empty_expression_is_refused(db):
    with pytest.raises(exceptions.InvalidSavedSearch):
        db.ops.save_search("   ")


def test_named_first_alphabetically_then_unnamed_by_expression(db):
    db.ops.save_search("width > 3")
    db.ops.save_search("width > 2", "b")
    db.ops.save_search("width > 1", "A")
    db.ops.save_search("height > 1")
    labels = [s.label for s in db.get_saved_searches()]
    assert labels == ["A", "b", "height > 1", "width > 3"]


def test_delete(db):
    db.ops.save_search("width > 100", "wide")
    db.ops.delete_saved_search("width > 100")
    assert db.get_saved_searches() == []
    db.ops.delete_saved_search("width > 100")


def test_a_search_naming_a_deleted_property_stays_but_no_longer_applies(db):
    db.prop_type_add("rank_for_test", "int", 0, False)
    saved = db.ops.save_search("`rank_for_test` > 1", "ranked")
    db.prop_type_del("rank_for_test")
    assert db.get_saved_searches() == [saved]
    with pytest.raises(exceptions.InvalidSourceExpression):
        db.validate_source_expression(saved.expression)
