"""Moving (merging) a video entry must not corrupt a unique property.

Regression test for the bug where `move_video_entries` ADD-ed the source entry's
property values onto the destination for *every* property, so a multiple=False
property holding different values on source and destination ended up with two
values — which later crashes on read (`from_strings`). The merge must now refuse
such a move and raise `UniquePropertyMergeConflict`.
"""

import pytest

from pysaurus.application.exceptions import UniquePropertyMergeConflict
from pysaurus.database.saurus.pysaurus_collection import PysaurusCollection


@pytest.fixture
def db(mem_saurus_database) -> PysaurusCollection:
    return mem_saurus_database


def _src_dst(db) -> tuple[int, int]:
    """Two videos set up as a move: src not-found, dst found."""
    ids = [v.video_id for v in db.get_videos(include=["video_id"])][:2]
    assert len(ids) == 2
    src, dst = ids
    db.videos_set_field("found", {src: False, dst: True})
    return src, dst


def test_move_refuses_divergent_unique_property(db):
    db.prop_type_add("u", "str", "", False)  # unique
    src, dst = _src_dst(db)
    db.videos_tag_set("u", {src: ["A"]})
    db.videos_tag_set("u", {dst: ["B"]})

    with pytest.raises(UniquePropertyMergeConflict):
        db.algos.move_video_entries([(src, dst)])

    # Refused before any write: src survives, dst keeps its own single value.
    assert db.videos_tag_get("u", indices=[dst])[dst] == ["B"]
    assert db.videos_tag_get("u", indices=[src])[src] == ["A"]


def test_move_allows_same_unique_value(db):
    db.prop_type_add("u", "str", "", False)
    src, dst = _src_dst(db)
    db.videos_tag_set("u", {src: ["same"]})
    db.videos_tag_set("u", {dst: ["same"]})

    db.algos.move_video_entries([(src, dst)])  # identical value -> no conflict

    assert db.videos_tag_get("u", indices=[dst])[dst] == ["same"]


def test_move_fills_empty_unique_destination(db):
    db.prop_type_add("u", "str", "", False)
    src, dst = _src_dst(db)
    db.videos_tag_set("u", {src: ["from_src"]})
    # dst has no value for u -> the source value just fills it.

    db.algos.move_video_entries([(src, dst)])

    assert db.videos_tag_get("u", indices=[dst])[dst] == ["from_src"]


def test_move_unions_multiple_property(db):
    db.prop_type_add("m", "str", "", True)  # multiple: union is fine
    src, dst = _src_dst(db)
    db.videos_tag_set("m", {src: ["a"]})
    db.videos_tag_set("m", {dst: ["b"]})

    db.algos.move_video_entries([(src, dst)])

    assert sorted(db.videos_tag_get("m", indices=[dst])[dst]) == ["a", "b"]
