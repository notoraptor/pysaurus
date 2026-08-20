"""
Tests for redundant property values: detection against a video's own titles,
and per-video removal.
"""

import os

import pytest

from pysaurus.core.functions import string_to_pieces

META_TITLE = "Titanic, avec Leonardo DiCaprio"


def _set_meta_title(db, video_id: int, title: str) -> None:
    """Set a meta title directly: it is not a writable field of the API."""
    db.db.modify(
        "UPDATE video SET meta_title = ? WHERE video_id = ?", [title, video_id]
    )


@pytest.fixture
def db_with_titles(mem_saurus_database):
    """A database with text/int properties and one controlled meta title."""
    db = mem_saurus_database
    db.prop_type_add("actor", "str", "", True)
    db.prop_type_add("source", "str", "", False)
    db.prop_type_add("rating", "int", 0, False)
    videos = db.get_videos(include=["video_id"])[:3]
    ids = [v.video_id for v in videos]
    _set_meta_title(db, ids[0], META_TITLE)
    return db, ids


def _find(db, video_id, **kwargs):
    """Return the redundant values of a single video."""
    return db.algos.find_redundant_property_values([video_id], **kwargs).get(
        video_id, {}
    )


class TestFindRedundantPropertyValues:
    def test_value_in_meta_title_is_redundant(self, db_with_titles):
        db, ids = db_with_titles
        db.videos_tag_set("actor", {ids[0]: ["Leonardo DiCaprio"]})

        assert _find(db, ids[0]) == {"actor": ["Leonardo DiCaprio"]}

    def test_case_punctuation_and_separators_do_not_matter(self, db_with_titles):
        db, ids = db_with_titles
        db.videos_tag_set("actor", {ids[0]: ["titanic, AVEC leonardo"]})

        assert _find(db, ids[0]) == {"actor": ["titanic, AVEC leonardo"]}

    def test_value_must_split_into_words_like_the_title_does(self, db_with_titles):
        db, ids = db_with_titles
        # The title spells "DiCaprio", which splits into "di" + "caprio"; the
        # value spells it as one word, so it is left alone rather than removed.
        db.videos_tag_set("actor", {ids[0]: ["leonardo-dicaprio"]})

        assert _find(db, ids[0]) == {}

    def test_value_absent_from_titles_is_kept(self, db_with_titles):
        db, ids = db_with_titles
        db.videos_tag_set("actor", {ids[0]: ["Kate Winslet"]})

        assert _find(db, ids[0]) == {}

    def test_only_whole_words_match(self, db_with_titles):
        db, ids = db_with_titles
        # "eonardo" is a substring of "Leonardo", but not a word of it.
        db.videos_tag_set("actor", {ids[0]: ["eonardo"]})

        assert _find(db, ids[0]) == {}

    def test_redundant_values_are_separated_from_kept_ones(self, db_with_titles):
        db, ids = db_with_titles
        db.videos_tag_set("actor", {ids[0]: ["Leonardo DiCaprio", "Kate Winslet"]})

        assert _find(db, ids[0]) == {"actor": ["Leonardo DiCaprio"]}

    def test_value_in_file_title_is_redundant(self, db_with_titles):
        db, ids = db_with_titles
        (video,) = db.get_videos(where={"video_id": ids[1]})
        word = string_to_pieces(video.file_title)[0]
        db.videos_tag_set("actor", {ids[1]: [word]})

        assert _find(db, ids[1]) == {"actor": [word]}

    def test_value_cannot_straddle_the_two_titles(self, db_with_titles):
        db, ids = db_with_titles
        (video,) = db.get_videos(where={"video_id": ids[1]})
        last_word = string_to_pieces(video.file_title)[-1]
        _set_meta_title(db, ids[1], "Winslet")
        db.videos_tag_set("actor", {ids[1]: [f"{last_word} Winslet"]})

        assert _find(db, ids[1]) == {}

    def test_non_text_property_is_ignored(self, db_with_titles):
        db, ids = db_with_titles
        # 1997 is in neither title, but the point is that ints are never scanned.
        _set_meta_title(db, ids[0], f"{META_TITLE} 1997")
        db.videos_tag_set("rating", {ids[0]: [1997]})

        assert _find(db, ids[0]) == {}

    def test_unique_property_is_scanned_too(self, db_with_titles):
        db, ids = db_with_titles
        db.videos_tag_set("source", {ids[0]: ["Titanic"]})

        assert _find(db, ids[0]) == {"source": ["Titanic"]}

    def test_prop_names_restricts_the_scan(self, db_with_titles):
        db, ids = db_with_titles
        db.videos_tag_set("actor", {ids[0]: ["Leonardo DiCaprio"]})
        db.videos_tag_set("source", {ids[0]: ["Titanic"]})

        assert _find(db, ids[0], prop_names=["source"]) == {"source": ["Titanic"]}

    def test_several_videos_at_once(self, db_with_titles):
        db, ids = db_with_titles
        db.videos_tag_set("actor", {ids[0]: ["Leonardo DiCaprio"]})
        db.videos_tag_set("actor", {ids[1]: ["Kate Winslet"]})

        found = db.algos.find_redundant_property_values(ids)

        assert found == {ids[0]: {"actor": ["Leonardo DiCaprio"]}}

    def test_no_video_and_no_property(self, db_with_titles):
        db, ids = db_with_titles

        assert db.algos.find_redundant_property_values([]) == {}
        assert db.algos.find_redundant_property_values(ids, prop_names=[]) == {}


def _folder_word(video) -> str:
    """A word of the parent folders that the file title does not repeat."""
    title_words = set(string_to_pieces(video.file_title))
    folder_words = string_to_pieces(os.path.dirname(str(video.filename)))
    return next(word for word in reversed(folder_words) if word not in title_words)


class TestFullPathMode:
    def test_folder_name_counts_only_with_the_full_path(self, db_with_titles):
        db, ids = db_with_titles
        (video,) = db.get_videos(where={"video_id": ids[1]})
        folder = _folder_word(video)
        db.videos_tag_set("actor", {ids[1]: [folder]})

        assert _find(db, ids[1]) == {}
        assert _find(db, ids[1], use_full_path=True) == {"actor": [folder]}

    def test_extension_counts_only_with_the_full_path(self, db_with_titles):
        db, ids = db_with_titles
        (video,) = db.get_videos(where={"video_id": ids[1]})
        extension = string_to_pieces(str(video.filename))[-1]
        assert extension not in string_to_pieces(video.file_title)
        db.videos_tag_set("actor", {ids[1]: [extension]})

        assert _find(db, ids[1]) == {}
        assert _find(db, ids[1], use_full_path=True) == {"actor": [extension]}

    def test_full_path_also_keeps_what_the_title_alone_finds(self, db_with_titles):
        db, ids = db_with_titles
        (video,) = db.get_videos(where={"video_id": ids[1]})
        title_word = string_to_pieces(video.file_title)[0]
        folder = _folder_word(video)
        db.videos_tag_set("actor", {ids[1]: [title_word, folder]})

        assert _find(db, ids[1]) == {"actor": [title_word]}
        assert sorted(_find(db, ids[1], use_full_path=True)["actor"]) == sorted(
            [title_word, folder]
        )

    def test_meta_title_still_matched_on_its_own(self, db_with_titles):
        db, ids = db_with_titles
        db.videos_tag_set("actor", {ids[0]: ["Leonardo DiCaprio"]})

        assert _find(db, ids[0], use_full_path=True) == {"actor": ["Leonardo DiCaprio"]}


class TestDeletePropertyValuesForVideos:
    def test_removes_only_the_listed_values(self, db_with_titles):
        db, ids = db_with_titles
        db.videos_tag_set("actor", {ids[0]: ["Leonardo DiCaprio", "Kate Winslet"]})

        count = db.algos.delete_property_values_for_videos(
            {ids[0]: {"actor": ["Leonardo DiCaprio"]}}
        )

        assert count == 1
        assert db.videos_tag_get("actor", indices=[ids[0]])[ids[0]] == ["Kate Winslet"]

    def test_leaves_other_videos_alone(self, db_with_titles):
        db, ids = db_with_titles
        db.videos_tag_set("actor", {ids[0]: ["Leonardo DiCaprio"]})
        db.videos_tag_set("actor", {ids[1]: ["Leonardo DiCaprio"]})

        db.algos.delete_property_values_for_videos(
            {ids[0]: {"actor": ["Leonardo DiCaprio"]}}
        )

        assert db.videos_tag_get("actor", indices=[ids[0]]).get(ids[0], []) == []
        assert db.videos_tag_get("actor", indices=[ids[1]])[ids[1]] == [
            "Leonardo DiCaprio"
        ]

    def test_removes_across_several_properties_and_videos(self, db_with_titles):
        db, ids = db_with_titles
        db.videos_tag_set("actor", {ids[0]: ["Leonardo DiCaprio"]})
        db.videos_tag_set("source", {ids[0]: ["Titanic"]})
        db.videos_tag_set("actor", {ids[1]: ["Kate Winslet"]})

        count = db.algos.delete_property_values_for_videos(
            {
                ids[0]: {"actor": ["Leonardo DiCaprio"], "source": ["Titanic"]},
                ids[1]: {"actor": ["Kate Winslet"]},
            }
        )

        assert count == 3
        assert db.videos_tag_get("actor").get(ids[0], []) == []
        assert db.videos_tag_get("source").get(ids[0], []) == []
        assert db.videos_tag_get("actor").get(ids[1], []) == []

    def test_empty_removals_do_nothing(self, db_with_titles):
        db, ids = db_with_titles
        db.videos_tag_set("actor", {ids[0]: ["Leonardo DiCaprio"]})

        assert db.algos.delete_property_values_for_videos({}) == 0
        assert db.algos.delete_property_values_for_videos({ids[0]: {"actor": []}}) == 0
        assert db.videos_tag_get("actor")[ids[0]] == ["Leonardo DiCaprio"]

    def test_removal_clears_what_find_reported(self, db_with_titles):
        db, ids = db_with_titles
        db.videos_tag_set("actor", {ids[0]: ["Leonardo DiCaprio", "Kate Winslet"]})
        db.videos_tag_set("source", {ids[0]: ["Titanic"]})

        found = db.algos.find_redundant_property_values(ids)
        db.algos.delete_property_values_for_videos(found)

        assert db.algos.find_redundant_property_values(ids) == {}
        assert db.videos_tag_get("actor")[ids[0]] == ["Kate Winslet"]
