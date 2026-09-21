"""``copy_similarity_infos``: one video's collection data lands on a similar
one, nothing is deleted, and the database settings drive the two policies."""

import pytest

from pysaurus.application import exceptions
from pysaurus.database.database_settings import DatabaseSettings
from pysaurus.database.saurus.pysaurus_collection import PysaurusCollection

TS_OLD = 1_546_300_800.0  # 2019-01-01 UTC
TS_NEW = 1_767_225_600.0  # 2026-01-01 UTC
INCLUDE = (
    "video_id",
    "filename",
    "meta_title",
    "watched",
    "date_added",
    "date_entry_opened",
    "properties",
)


@pytest.fixture
def db(mem_saurus_database) -> PysaurusCollection:
    """The fixture database with a multiple string property set as title target."""
    mem_saurus_database.prop_type_add("titles", "str", "", True)
    mem_saurus_database.ops.set_settings(
        DatabaseSettings(generalize_title_property="titles")
    )
    return mem_saurus_database


def _pair(db: PysaurusCollection) -> tuple[int, int]:
    src, dst = [v.video_id for v in db.get_videos(include=["video_id"])][:2]
    return src, dst


def _video(db: PysaurusCollection, video_id: int):
    (video,) = db.get_videos(include=INCLUDE, where={"video_id": video_id})
    return video


def _set_meta_title(db: PysaurusCollection, video_id: int, title: str) -> None:
    db.db.modify(
        "UPDATE video SET meta_title = ? WHERE video_id = ?", [title, video_id]
    )


def test_multiple_property_is_unioned(db):
    db.prop_type_add("m", "str", "", True)
    src, dst = _pair(db)
    db.videos_tag_set("m", {src: ["a"], dst: ["b"]})

    report = db.algos.copy_similarity_infos(src, dst)

    assert sorted(_video(db, dst).properties["m"]) == ["a", "b"]
    assert report.properties == ["m"]
    assert report.kept == []


def test_unique_property_fills_an_empty_destination(db):
    db.prop_type_add("u", "str", "", False)
    src, dst = _pair(db)
    db.videos_tag_set("u", {src: ["A"]})

    report = db.algos.copy_similarity_infos(src, dst)

    assert _video(db, dst).properties["u"] == ["A"]
    assert report.properties == ["u"]


def test_unique_property_keeps_the_destination_by_default(db):
    db.prop_type_add("u", "str", "", False)
    src, dst = _pair(db)
    db.videos_tag_set("u", {src: ["A"], dst: ["B"]})

    report = db.algos.copy_similarity_infos(src, dst)

    assert _video(db, dst).properties["u"] == ["B"]
    assert report.kept == ["u"]
    assert report.properties == []


def test_unique_property_is_overwritten_when_the_setting_says_so(db):
    db.prop_type_add("u", "str", "", False)
    db.ops.set_settings(
        DatabaseSettings(
            generalize_title_property="titles", copy_overwrites_unique_properties=True
        )
    )
    src, dst = _pair(db)
    db.videos_tag_set("u", {src: ["A"], dst: ["B"]})

    report = db.algos.copy_similarity_infos(src, dst)

    assert _video(db, dst).properties["u"] == ["A"]
    assert report.properties == ["u"]
    assert report.kept == []


def test_values_already_there_are_not_reported(db):
    db.prop_type_add("u", "str", "", False)
    src, dst = _pair(db)
    db.videos_tag_set("u", {src: ["same"], dst: ["same"]})
    # Both fixture videos also share category=["other"].

    report = db.algos.copy_similarity_infos(src, dst, with_titles=False)

    assert report.properties == []
    assert report.kept == []


def test_titles_stack_into_the_configured_property(db):
    src, dst = _pair(db)
    _set_meta_title(db, src, "Meta title of source")
    file_title = _video(db, src).file_title

    report = db.algos.copy_similarity_infos(src, dst)

    assert sorted(_video(db, dst).properties["titles"]) == sorted(
        [file_title, "Meta title of source"]
    )
    assert report.titles == [file_title, "Meta title of source"]
    assert "titles" not in _video(db, src).properties  # source untouched


def test_titles_are_deduplicated(db):
    src, dst = _pair(db)
    file_title = _video(db, src).file_title
    _set_meta_title(db, src, file_title)

    report = db.algos.copy_similarity_infos(src, dst)

    assert _video(db, dst).properties["titles"] == [file_title]
    assert report.titles == [file_title]


def test_titles_already_present_are_not_reported(db):
    src, dst = _pair(db)
    file_title = _video(db, src).file_title
    db.videos_tag_set("titles", {dst: [file_title]})

    report = db.algos.copy_similarity_infos(src, dst)

    assert _video(db, dst).properties["titles"] == [file_title]
    assert report.titles == []


def test_titles_need_a_configured_property(db):
    db.ops.set_settings(DatabaseSettings())
    src, dst = _pair(db)

    with pytest.raises(exceptions.NoTitleProperty):
        db.algos.copy_similarity_infos(src, dst)

    report = db.algos.copy_similarity_infos(src, dst, with_titles=False)
    assert report.titles == []
    assert "titles" not in _video(db, dst).properties


def test_titles_need_a_multiple_property(db):
    db.prop_type_add("single", "str", "", False)
    db.ops.set_settings(DatabaseSettings(generalize_title_property="single"))
    src, dst = _pair(db)

    with pytest.raises(exceptions.NoTitleProperty):
        db.algos.copy_similarity_infos(src, dst)


def test_watched_never_turns_off(db):
    src, dst = _pair(db)
    db.videos_set_field("watched", {src: True, dst: False})
    report = db.algos.copy_similarity_infos(src, dst)
    assert _video(db, dst).watched is True
    assert report.watched is True

    db.videos_set_field("watched", {src: False, dst: True})
    report = db.algos.copy_similarity_infos(src, dst)
    assert _video(db, dst).watched is True
    assert report.watched is False


@pytest.mark.parametrize(
    "src_date,dst_date,expected,changed",
    [
        (TS_OLD, TS_NEW, TS_OLD, True),
        (TS_NEW, TS_OLD, TS_OLD, False),
        (0.0, TS_NEW, TS_NEW, False),
        (TS_OLD, 0.0, TS_OLD, True),
    ],
)
def test_date_added_keeps_the_earliest_known(db, src_date, dst_date, expected, changed):
    src, dst = _pair(db)
    db.videos_set_field("date_added", {src: src_date, dst: dst_date})

    report = db.algos.copy_similarity_infos(src, dst)

    assert _video(db, dst).date_added == expected
    assert report.date_added is changed


def test_date_entry_opened_keeps_the_latest(db):
    src, dst = _pair(db)
    db.videos_set_field("date_entry_opened", {src: TS_NEW, dst: TS_OLD})
    db.algos.copy_similarity_infos(src, dst)
    assert _video(db, dst).date_entry_opened.time == TS_NEW

    db.videos_set_field("date_entry_opened", {src: TS_OLD, dst: TS_NEW})
    db.algos.copy_similarity_infos(src, dst)
    assert _video(db, dst).date_entry_opened.time == TS_NEW


def test_source_survives_untouched(db):
    db.prop_type_add("u", "str", "", False)
    src, dst = _pair(db)
    db.videos_tag_set("u", {src: ["A"]})
    db.videos_set_field("watched", {src: True})
    before = _video(db, src)

    db.algos.copy_similarity_infos(src, dst)

    after = _video(db, src)
    assert after.properties == before.properties
    assert after.watched == before.watched
    assert after.date_added == before.date_added
    assert db.count_videos(where={"video_id": [src, dst]}) == 2


def test_copying_onto_itself_is_refused(db):
    src, _ = _pair(db)
    with pytest.raises(ValueError):
        db.algos.copy_similarity_infos(src, src)
