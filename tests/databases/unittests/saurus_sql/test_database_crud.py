"""
Tests for database CRUD operations on the SQL backend.

These tests cover property type operations, video property operations,
field operations, validation, and other write operations that were
previously only tested through JSON vs SQL comparison tests.

Uses mem_saurus_database (small in-memory SQL DB) for write tests
and fake_saurus_database for read-only tests.
"""

import pytest

from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.database.saurus.sql.pysaurus_collection import PysaurusCollection


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def db(mem_saurus_database) -> PysaurusCollection:
    """Writable in-memory SQL database."""
    return mem_saurus_database


@pytest.fixture
def ro_db(fake_saurus_database) -> PysaurusCollection:
    """Read-only SQL database."""
    return fake_saurus_database


# =============================================================================
# Basic info
# =============================================================================


class TestBasicInfo:
    """Test basic database info methods."""

    def test_get_name(self, ro_db):
        name = ro_db.get_name()
        assert isinstance(name, str)
        assert len(name) > 0

    def test_get_folders(self, ro_db):
        folders = list(ro_db.get_folders())
        assert len(folders) > 0
        for f in folders:
            assert str(f)


# =============================================================================
# Property type CRUD
# =============================================================================


class TestPropertyTypeCRUD:
    """Test property type create, read, update, delete operations."""

    def test_prop_type_add_string(self, db):
        db.prop_type_add("test_tags", "str", "", True)
        props = db.get_prop_types(name="test_tags")
        assert len(props) == 1
        assert props[0]["name"] == "test_tags"
        assert bool(props[0]["multiple"]) is True

    def test_prop_type_add_int(self, db):
        db.prop_type_add("rating", "int", 0, False)
        props = db.get_prop_types(name="rating")
        assert len(props) == 1
        assert bool(props[0]["multiple"]) is False

    def test_prop_type_add_enum(self, db):
        enum_values = ["low", "medium", "high"]
        db.prop_type_add("quality", "str", enum_values, False)
        props = db.get_prop_types(name="quality")
        assert len(props) == 1
        assert set(props[0]["enumeration"]) == set(enum_values)

    def test_prop_type_del(self, db):
        db.prop_type_add("temp_prop", "str", "", True)
        assert len(db.get_prop_types(name="temp_prop")) == 1

        db.prop_type_del("temp_prop")
        assert len(db.get_prop_types(name="temp_prop")) == 0

    def test_prop_type_set_name(self, db):
        db.prop_type_add("old_prop", "str", "", True)
        db.prop_type_set_name("old_prop", "new_prop")

        assert len(db.get_prop_types(name="old_prop")) == 0
        assert len(db.get_prop_types(name="new_prop")) == 1

    def test_prop_type_set_multiple(self, db):
        db.prop_type_add("tags", "str", "", False)
        assert bool(db.get_prop_types(name="tags")[0]["multiple"]) is False

        db.prop_type_set_multiple("tags", True)
        assert bool(db.get_prop_types(name="tags")[0]["multiple"]) is True


# =============================================================================
# get_prop_types
# =============================================================================


class TestGetPropTypes:
    """Test get_prop_types method."""

    def test_get_all(self, ro_db):
        props = ro_db.get_prop_types()
        assert isinstance(props, list)
        for p in props:
            assert "name" in p

    def test_get_by_name(self, ro_db):
        all_props = ro_db.get_prop_types()
        if all_props:
            name = all_props[0]["name"]
            by_name = ro_db.get_prop_types(name=name)
            assert len(by_name) == 1
            assert by_name[0]["name"] == name


# =============================================================================
# get_video_filename
# =============================================================================


class TestGetVideoFilename:
    """Test ops.get_video_filename method."""

    def test_get_video_filename(self, ro_db):
        videos = ro_db.get_videos(include=["video_id", "filename"])
        for video in videos[:5]:
            filename = ro_db.ops.get_video_filename(video.video_id)
            assert str(filename) == str(video.filename)


# =============================================================================
# videos_get_terms
# =============================================================================


class TestVideosGetTerms:
    """Test videos_get_terms method."""

    def test_returns_dict(self, ro_db):
        terms = ro_db.videos_get_terms()
        assert isinstance(terms, dict)
        assert len(terms) > 0

    def test_keys_are_video_ids(self, ro_db):
        terms = ro_db.videos_get_terms()
        video_ids = {v.video_id for v in ro_db.get_videos(include=["video_id"])}
        assert set(terms.keys()).issubset(video_ids)

    def test_values_are_string_lists(self, ro_db):
        terms = ro_db.videos_get_terms()
        for video_id, term_list in list(terms.items())[:10]:
            assert isinstance(term_list, list)
            for term in term_list:
                assert isinstance(term, str)


# =============================================================================
# videos_get_moves / get_unique_moves
# =============================================================================


class TestVideosGetMoves:
    """Test videos_get_moves and get_unique_moves methods."""

    def test_videos_get_moves(self, ro_db):
        moves = list(ro_db.videos_get_moves())
        assert isinstance(moves, list)
        for video_id, move_list in moves:
            assert isinstance(video_id, int)
            assert isinstance(move_list, list)

    def test_get_unique_moves(self, ro_db):
        unique_moves = ro_db.algos.get_unique_moves()
        assert isinstance(unique_moves, list)
        for from_id, to_id in unique_moves:
            assert isinstance(from_id, int)
            assert isinstance(to_id, int)


# =============================================================================
# videos_tag_get
# =============================================================================


class TestVideosTagGet:
    """Test videos_tag_get method."""

    def test_get_all(self, ro_db):
        all_props = ro_db.get_prop_types()
        for prop in all_props:
            tags = ro_db.videos_tag_get(prop["name"])
            assert isinstance(tags, dict)

    def test_get_with_indices(self, ro_db):
        all_props = ro_db.get_prop_types()
        videos = ro_db.get_videos(include=["video_id"])
        sample_ids = [v.video_id for v in videos[:10]]

        for prop in all_props:
            tags = ro_db.videos_tag_get(prop["name"], indices=sample_ids)
            assert isinstance(tags, dict)
            # All returned keys should be in sample_ids
            assert set(tags.keys()).issubset(set(sample_ids))


# =============================================================================
# Video property operations
# =============================================================================


class TestVideoPropertyOperations:
    """Test setting properties on videos."""

    def test_videos_tag_set_single(self, db):
        db.prop_type_add("test_cat", "str", "", True)
        video_id = db.get_videos(include=["video_id"])[0].video_id

        db.videos_tag_set("test_cat", {video_id: ["value1"]})
        tags = db.videos_tag_get("test_cat", indices=[video_id])
        assert tags[video_id] == ["value1"]

    def test_videos_tag_set_multiple(self, db):
        db.prop_type_add("test_cat", "str", "", True)
        videos = db.get_videos(include=["video_id"])[:10]
        updates = {v.video_id: ["val_a"] for v in videos}

        db.videos_tag_set("test_cat", updates)

        for v in videos:
            tags = db.videos_tag_get("test_cat", indices=[v.video_id])
            assert tags[v.video_id] == ["val_a"]

    def test_videos_tag_set_merge(self, db):
        db.prop_type_add("test_cat", "str", "", True)
        video_id = db.get_videos(include=["video_id"])[0].video_id

        db.videos_tag_set("test_cat", {video_id: ["value1"]})
        db.videos_tag_set(
            "test_cat", {video_id: ["value2"]}, action=AbstractDatabase.action.ADD
        )

        tags = db.videos_tag_get("test_cat", indices=[video_id])
        assert sorted(tags[video_id]) == ["value1", "value2"]

    def test_video_entry_set_tags(self, db):
        db.prop_type_add("tag_a", "str", "", True)
        db.prop_type_add("tag_b", "str", "", False)
        video_id = db.get_videos(include=["video_id"])[0].video_id

        db.video_entry_set_tags(video_id, {"tag_a": ["x", "y"], "tag_b": ["z"]})

        tags_a = db.videos_tag_get("tag_a", indices=[video_id])
        tags_b = db.videos_tag_get("tag_b", indices=[video_id])
        assert sorted(tags_a[video_id]) == ["x", "y"]
        assert tags_b[video_id] == ["z"]


# =============================================================================
# videos_set_field
# =============================================================================


class TestVideosSetField:
    """Test videos_set_field for various fields."""

    def test_set_watched(self, db):
        video_id = db.get_videos(include=["video_id"])[0].video_id
        db.videos_set_field("watched", {video_id: True})
        video = db.get_videos(where={"video_id": video_id})[0]
        assert video.watched is True

    def test_set_similarity_id(self, db):
        video_id = db.get_videos(include=["video_id"])[0].video_id
        db.videos_set_field("similarity_id", {video_id: 12345})
        video = db.get_videos(where={"video_id": video_id})[0]
        assert video.similarity_id == 12345

    def test_set_multiple_videos(self, db):
        videos = db.get_videos(include=["video_id"])[:10]
        changes = {v.video_id: True for v in videos}
        db.videos_set_field("watched", changes)

        for v in videos:
            video = db.get_videos(where={"video_id": v.video_id})[0]
            assert video.watched is True


# =============================================================================
# Property value operations (via DatabaseAlgorithms / DatabaseOperations)
# =============================================================================


class TestPropertyValueOperations:
    """Test property value manipulation operations."""

    @pytest.fixture
    def db_with_tags(self, db):
        """Setup database with a 'tags' property and some values."""
        db.prop_type_add("tags", "str", "", True)
        videos = db.get_videos(include=["video_id"])[:20]
        updates = {v.video_id: ["alpha", "beta"] for v in videos}
        db.videos_tag_set("tags", updates)
        return db, [v.video_id for v in videos]

    def test_delete_property_values(self, db_with_tags):
        db, video_ids = db_with_tags
        db.algos.delete_property_values("tags", ["beta"])

        for vid in video_ids[:5]:
            tags = db.videos_tag_get("tags", indices=[vid])
            assert "beta" not in tags[vid]
            assert "alpha" in tags[vid]

    def test_replace_property_values(self, db_with_tags):
        db, video_ids = db_with_tags
        result = db.algos.replace_property_values("tags", ["beta"], "gamma")
        assert result is True

        for vid in video_ids[:5]:
            tags = db.videos_tag_get("tags", indices=[vid])
            assert "beta" not in tags[vid]
            assert "gamma" in tags[vid]

    def test_count_property_for_videos(self, db_with_tags):
        db, video_ids = db_with_tags
        count = db.ops.count_property_for_videos(video_ids, "tags")
        count_dict = dict(count)
        assert count_dict["alpha"] == len(video_ids)
        assert count_dict["beta"] == len(video_ids)

    def test_update_property_for_videos(self, db_with_tags):
        db, video_ids = db_with_tags
        subset = video_ids[:10]
        db.ops.update_property_for_videos(
            subset, "tags", values_to_add=["new_val"], values_to_remove=["beta"]
        )

        for vid in subset:
            tags = db.videos_tag_get("tags", indices=[vid])
            assert "beta" not in tags[vid]
            assert "new_val" in tags[vid]


# =============================================================================
# Validation
# =============================================================================


class TestValidation:
    """Test validate_prop_values method."""

    def test_validate_string(self, db):
        db.prop_type_add("test_str", "str", "", True)
        result = db.ops.validate_prop_values("test_str", ["val1", "val2"])
        assert result == ["val1", "val2"]

    def test_validate_int(self, db):
        db.prop_type_add("test_int", "int", 0, False)
        result = db.ops.validate_prop_values("test_int", [42])
        assert result == [42]

    def test_validate_enum(self, db):
        db.prop_type_add("test_enum", "str", ["a", "b", "c"], False)
        result = db.ops.validate_prop_values("test_enum", ["a"])
        assert result == ["a"]


# =============================================================================
# set_property_for_videos
# =============================================================================


class TestSetPropertyForVideos:
    """Test set_property_for_videos method."""

    def test_set_property(self, db):
        db.prop_type_add("custom", "str", "", True)
        videos = db.get_videos(include=["video_id"])[:10]
        video_ids = [v.video_id for v in videos]
        updates = {vid: ["custom_val"] for vid in video_ids}

        db.ops.set_property_for_videos("custom", updates)

        tags = db.videos_tag_get("custom", indices=video_ids)
        for vid in video_ids:
            assert tags[vid] == ["custom_val"]

    def test_set_property_merge(self, db):
        db.prop_type_add("merge_tag", "str", "", True)
        video_id = db.get_videos(include=["video_id"])[0].video_id

        db.ops.set_property_for_videos("merge_tag", {video_id: ["a"]})
        db.ops.set_property_for_videos("merge_tag", {video_id: ["b"]}, merge=True)

        tags = db.videos_tag_get("merge_tag", indices=[video_id])
        assert sorted(tags[video_id]) == ["a", "b"]


# =============================================================================
# Mark as watched / read
# =============================================================================


class TestWatchOperations:
    """Test mark_as_watched and mark_as_read methods."""

    def test_mark_as_watched(self, db):
        video_id = db.get_videos(include=["video_id"])[0].video_id
        db.ops.mark_as_watched(video_id)

        video = db.get_videos(where={"video_id": video_id})[0]
        assert bool(video.watched) is True
        assert video.date_entry_opened.time > 0

    def test_mark_as_read_toggle(self, db):
        video_id = db.get_videos(include=["video_id"])[0].video_id
        initial = db.get_videos(where={"video_id": video_id})[0].watched

        result1 = db.ops.mark_as_read(video_id)
        assert result1 == (not initial)

        result2 = db.ops.mark_as_read(video_id)
        assert result2 == initial


# =============================================================================
# Similarity operations
# =============================================================================


class TestSimilarityOperations:
    """Test similarity-related operations."""

    def test_set_similarities(self, db):
        videos = db.get_videos(include=["video_id"])[:5]
        video_ids = [v.video_id for v in videos]
        similarities = {vid: 100 for vid in video_ids}

        db.ops.set_similarities(similarities)

        for vid in video_ids:
            video = db.get_videos(where={"video_id": vid})[0]
            assert video.similarity_id == 100

    def test_set_similarities_from_list(self, db):
        videos = db.get_videos(include=["video_id"])[:3]
        video_ids = [v.video_id for v in videos]
        sim_ids = [1, 2, 3]

        db.ops.set_similarities_from_list(video_ids, sim_ids)

        for vid, expected_sim in zip(video_ids, sim_ids):
            video = db.get_videos(where={"video_id": vid})[0]
            assert video.similarity_id == expected_sim


# =============================================================================
# Video entry delete
# =============================================================================


class TestVideoEntryDel:
    """Test video_entry_del method."""

    def test_delete_video_entry(self, db):
        videos = db.get_videos(include=["video_id"])
        video_id = videos[0].video_id
        count_before = len(videos)

        db.video_entry_del(video_id)

        count_after = len(db.get_videos(include=["video_id"]))
        assert count_after == count_before - 1

        remaining_ids = {v.video_id for v in db.get_videos(include=["video_id"])}
        assert video_id not in remaining_ids


# =============================================================================
# Thumbnails
# =============================================================================


class TestThumbnails:
    """Test thumbnail-related operations."""

    def test_thumbnail_presence(self, ro_db):
        videos = ro_db.get_videos()
        for v in videos:
            assert isinstance(v.with_thumbnails, (bool, int))

    def test_thumbnail_data(self, ro_db):
        videos_with = ro_db.get_videos(where={"with_thumbnails": True})
        for v in videos_with[:5]:
            thumb = v.thumbnail
            if thumb is not None:
                assert isinstance(thumb, bytes)
                assert len(thumb) > 0
