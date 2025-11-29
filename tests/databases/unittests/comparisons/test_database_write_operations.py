"""
Tests for write operations on JSON and NewSQL databases.

These tests use temporary copies of the databases (mem_old_database, mem_new_database)
to ensure original files are not modified.

Tests cover:
- Property type operations (add, delete, rename, set_multiple)
- Video property operations (videos_tag_set, video_entry_set_tags)
- Field operations (videos_set_field)
- Property value operations (delete, replace, count, update, fill_property_with_terms)
- Validation (validate_prop_values)
"""

import pytest

from pysaurus.database.abstract_database import AbstractDatabase


def get_category_from_filename(filename: str) -> str:
    """Extract category from video filename path (parent folder name)."""
    # Filename is like: .../test_videos/action/test_000001_320x240.mp4
    parts = filename.replace("\\", "/").split("/")
    # Find test_videos and get next part
    for i, part in enumerate(parts):
        if part == "test_videos" and i + 1 < len(parts):
            return parts[i + 1]
    return "unknown"


class TestPropertyTypeOperations:
    """Test property type CRUD operations."""

    def test_prop_type_add_string(self, mem_old_database, mem_new_database):
        """Both should support adding a string property type."""
        prop_name = "test_tags"

        # Add property type (prop_type must be string name, not the type itself)
        mem_old_database.prop_type_add(prop_name, "str", "", True)
        mem_new_database.prop_type_add(prop_name, "str", "", True)

        # Verify
        old_props = mem_old_database.get_prop_types(name=prop_name)
        new_props = mem_new_database.get_prop_types(name=prop_name)

        assert len(old_props) == len(new_props) == 1
        assert old_props[0]["name"] == new_props[0]["name"] == prop_name
        assert old_props[0]["multiple"] is new_props[0]["multiple"] is True

    def test_prop_type_add_int(self, mem_old_database, mem_new_database):
        """Both should support adding an integer property type."""
        prop_name = "rating"

        mem_old_database.prop_type_add(prop_name, "int", 0, False)
        mem_new_database.prop_type_add(prop_name, "int", 0, False)

        old_props = mem_old_database.get_prop_types(name=prop_name)
        new_props = mem_new_database.get_prop_types(name=prop_name)

        assert len(old_props) == len(new_props) == 1
        assert old_props[0]["multiple"] is new_props[0]["multiple"] is False

    def test_prop_type_add_enum(self, mem_old_database, mem_new_database):
        """Both should support adding an enum property type."""
        prop_name = "quality"
        enum_values = ["low", "medium", "high"]

        mem_old_database.prop_type_add(prop_name, "str", enum_values, False)
        mem_new_database.prop_type_add(prop_name, "str", enum_values, False)

        old_props = mem_old_database.get_prop_types(name=prop_name)
        new_props = mem_new_database.get_prop_types(name=prop_name)

        assert len(old_props) == len(new_props) == 1
        # Enum values may be stored in different order, compare as sets
        assert (
            set(old_props[0]["enumeration"])
            == set(new_props[0]["enumeration"])
            == set(enum_values)
        )

    def test_prop_type_del(self, mem_old_database, mem_new_database):
        """Both should support deleting a property type."""
        prop_name = "temp_prop"

        # Add then delete
        mem_old_database.prop_type_add(prop_name, "str", "", True)
        mem_new_database.prop_type_add(prop_name, "str", "", True)

        mem_old_database.prop_type_del(prop_name)
        mem_new_database.prop_type_del(prop_name)

        # Verify deleted
        old_props = mem_old_database.get_prop_types(name=prop_name)
        new_props = mem_new_database.get_prop_types(name=prop_name)

        assert len(old_props) == len(new_props) == 0

    def test_prop_type_set_name(self, mem_old_database, mem_new_database):
        """Both should support renaming a property type."""
        old_name = "old_prop"
        new_name = "new_prop"

        # Add property
        mem_old_database.prop_type_add(old_name, "str", "", True)
        mem_new_database.prop_type_add(old_name, "str", "", True)

        # Rename
        mem_old_database.prop_type_set_name(old_name, new_name)
        mem_new_database.prop_type_set_name(old_name, new_name)

        # Verify old name gone, new name exists
        assert len(mem_old_database.get_prop_types(name=old_name)) == 0
        assert len(mem_new_database.get_prop_types(name=old_name)) == 0
        assert len(mem_old_database.get_prop_types(name=new_name)) == 1
        assert len(mem_new_database.get_prop_types(name=new_name)) == 1

    def test_prop_type_set_multiple(self, mem_old_database, mem_new_database):
        """Both should support changing the multiple flag."""
        prop_name = "tags"

        # Add as single value
        mem_old_database.prop_type_add(prop_name, "str", "", False)
        mem_new_database.prop_type_add(prop_name, "str", "", False)

        # Change to multiple
        mem_old_database.prop_type_set_multiple(prop_name, True)
        mem_new_database.prop_type_set_multiple(prop_name, True)

        old_props = mem_old_database.get_prop_types(name=prop_name)
        new_props = mem_new_database.get_prop_types(name=prop_name)

        assert old_props[0]["multiple"] is new_props[0]["multiple"] is True


class TestVideoPropertyOperations:
    """Test setting properties on videos."""

    @pytest.fixture
    def databases_with_category(self, mem_old_database, mem_new_database):
        """Setup databases with a 'test_category' property."""
        prop_name = "test_category"
        mem_old_database.prop_type_add(prop_name, "str", "", True)
        mem_new_database.prop_type_add(prop_name, "str", "", True)
        return mem_old_database, mem_new_database, prop_name

    def test_videos_tag_set_single_video(self, databases_with_category):
        """Both should set property for a single video."""
        old_db, new_db, prop_name = databases_with_category

        # Get a sample video
        old_videos = old_db.get_videos(include=["video_id", "filename"])
        video = old_videos[0]
        video_id = video.video_id
        category = get_category_from_filename(str(video.filename))

        # Set property
        old_db.videos_tag_set(prop_name, {video_id: [category]})
        new_db.videos_tag_set(prop_name, {video_id: [category]})

        # Verify
        old_tags = old_db.videos_tag_get(prop_name, indices=[video_id])
        new_tags = new_db.videos_tag_get(prop_name, indices=[video_id])

        assert old_tags[video_id] == new_tags[video_id] == [category]

    def test_videos_tag_set_multiple_videos(self, databases_with_category):
        """Both should set property for multiple videos."""
        old_db, new_db, prop_name = databases_with_category

        # Get sample videos
        old_videos = old_db.get_videos(include=["video_id", "filename"])[:100]

        # Build updates based on actual categories
        updates = {}
        for video in old_videos:
            category = get_category_from_filename(str(video.filename))
            updates[video.video_id] = [category]

        # Set properties
        old_db.videos_tag_set(prop_name, updates)
        new_db.videos_tag_set(prop_name, updates)

        # Verify
        video_ids = list(updates.keys())
        old_tags = old_db.videos_tag_get(prop_name, indices=video_ids)
        new_tags = new_db.videos_tag_get(prop_name, indices=video_ids)

        for video_id in video_ids:
            assert old_tags[video_id] == new_tags[video_id]

    def test_videos_tag_set_merge(self, databases_with_category):
        """Both should support merging property values."""
        old_db, new_db, prop_name = databases_with_category

        video_id = old_db.get_videos(include=["video_id"])[0].video_id

        # Set initial value
        old_db.videos_tag_set(prop_name, {video_id: ["value1"]})
        new_db.videos_tag_set(prop_name, {video_id: ["value1"]})

        # Merge with new value
        old_db.videos_tag_set(
            prop_name, {video_id: ["value2"]}, action=AbstractDatabase.action.ADD
        )
        new_db.videos_tag_set(
            prop_name, {video_id: ["value2"]}, action=AbstractDatabase.action.ADD
        )

        # Should have both values
        old_tags = old_db.videos_tag_get(prop_name, indices=[video_id])
        new_tags = new_db.videos_tag_get(prop_name, indices=[video_id])

        assert (
            sorted(old_tags[video_id])
            == sorted(new_tags[video_id])
            == ["value1", "value2"]
        )

    def test_video_entry_set_tags(self, databases_with_category):
        """Both should set multiple properties on a single video."""
        old_db, new_db, prop_name = databases_with_category

        # Add another property
        old_db.prop_type_add("resolution", "str", "", False)
        new_db.prop_type_add("resolution", "str", "", False)

        video = old_db.get_videos(include=["video_id", "filename", "width", "height"])[
            0
        ]
        video_id = video.video_id
        category = get_category_from_filename(str(video.filename))
        resolution = f"{video.width}x{video.height}"

        # Set multiple properties at once
        properties = {prop_name: [category], "resolution": [resolution]}
        old_db.video_entry_set_tags(video_id, properties)
        new_db.video_entry_set_tags(video_id, properties)

        # Verify both properties
        old_cat = old_db.videos_tag_get(prop_name, indices=[video_id])
        new_cat = new_db.videos_tag_get(prop_name, indices=[video_id])
        old_res = old_db.videos_tag_get("resolution", indices=[video_id])
        new_res = new_db.videos_tag_get("resolution", indices=[video_id])

        assert old_cat[video_id] == new_cat[video_id] == [category]
        assert old_res[video_id] == new_res[video_id] == [resolution]


class TestVideosSetField:
    """Test videos_set_field for various fields."""

    def test_set_watched(self, mem_old_database, mem_new_database):
        """Both should set the watched field."""
        video_id = mem_old_database.get_videos(include=["video_id"])[0].video_id

        mem_old_database.videos_set_field("watched", {video_id: True})
        mem_new_database.videos_set_field("watched", {video_id: True})

        old_video = mem_old_database.get_videos(where={"video_id": video_id})[0]
        new_video = mem_new_database.get_videos(where={"video_id": video_id})[0]

        assert old_video.watched is new_video.watched is True

    def test_set_similarity_id(self, mem_old_database, mem_new_database):
        """Both should set similarity_id."""
        videos = mem_old_database.get_videos(include=["video_id"])[:2]
        video_id = videos[0].video_id
        sim_id = 12345

        mem_old_database.videos_set_field("similarity_id", {video_id: sim_id})
        mem_new_database.videos_set_field("similarity_id", {video_id: sim_id})

        old_video = mem_old_database.get_videos(where={"video_id": video_id})[0]
        new_video = mem_new_database.get_videos(where={"video_id": video_id})[0]

        assert old_video.similarity_id == new_video.similarity_id == sim_id

    def test_set_multiple_fields(self, mem_old_database, mem_new_database):
        """Both should handle setting multiple videos at once."""
        videos = mem_old_database.get_videos(include=["video_id"])[:10]
        video_ids = [v.video_id for v in videos]

        changes = {vid: True for vid in video_ids}

        mem_old_database.videos_set_field("watched", changes)
        mem_new_database.videos_set_field("watched", changes)

        for vid in video_ids:
            old_v = mem_old_database.get_videos(where={"video_id": vid})[0]
            new_v = mem_new_database.get_videos(where={"video_id": vid})[0]
            assert old_v.watched is new_v.watched is True


class TestPropertyValueOperations:
    """Test property value manipulation operations."""

    @pytest.fixture
    def databases_with_tags(self, mem_old_database, mem_new_database):
        """Setup databases with a 'tags' property and some values."""
        prop_name = "tags"
        mem_old_database.prop_type_add(prop_name, "str", "", True)
        mem_new_database.prop_type_add(prop_name, "str", "", True)

        # Assign tags to videos based on category
        videos = mem_old_database.get_videos(include=["video_id", "filename"])[:50]
        updates = {}
        for video in videos:
            category = get_category_from_filename(str(video.filename))
            updates[video.video_id] = [category, "test_tag"]

        mem_old_database.videos_tag_set(prop_name, updates)
        mem_new_database.videos_tag_set(prop_name, updates)

        return mem_old_database, mem_new_database, prop_name, list(updates.keys())

    def test_delete_property_values(self, databases_with_tags):
        """Both should delete specific property values."""
        old_db, new_db, prop_name, video_ids = databases_with_tags

        # Delete "test_tag" from all videos
        old_db.algos.delete_property_values(prop_name, ["test_tag"])
        new_db.algos.delete_property_values(prop_name, ["test_tag"])

        # Verify "test_tag" is gone
        for vid in video_ids[:5]:
            old_tags = old_db.videos_tag_get(prop_name, indices=[vid])
            new_tags = new_db.videos_tag_get(prop_name, indices=[vid])
            assert "test_tag" not in old_tags[vid]
            assert "test_tag" not in new_tags[vid]

    def test_replace_property_values(self, databases_with_tags):
        """Both should replace property values."""
        old_db, new_db, prop_name, video_ids = databases_with_tags

        # Replace "test_tag" with "replaced_tag"
        old_result = old_db.algos.replace_property_values(
            prop_name, ["test_tag"], "replaced_tag"
        )
        new_result = new_db.algos.replace_property_values(
            prop_name, ["test_tag"], "replaced_tag"
        )

        assert old_result is new_result is True

        # Verify replacement
        for vid in video_ids[:5]:
            old_tags = old_db.videos_tag_get(prop_name, indices=[vid])
            new_tags = new_db.videos_tag_get(prop_name, indices=[vid])
            assert "test_tag" not in old_tags[vid]
            assert "test_tag" not in new_tags[vid]
            assert "replaced_tag" in old_tags[vid]
            assert "replaced_tag" in new_tags[vid]

    def test_count_property_for_videos(self, databases_with_tags):
        """Both should count property values the same way."""
        old_db, new_db, prop_name, video_ids = databases_with_tags

        old_count = old_db.ops.count_property_for_videos(video_ids, prop_name)
        new_count = new_db.ops.count_property_for_videos(video_ids, prop_name)

        # Should have same counts
        assert old_count == new_count
        # Should include test_tag with count == len(video_ids)
        count_dict = dict(old_count)
        assert count_dict.get("test_tag") == len(video_ids)

    def test_update_property_for_videos(self, databases_with_tags):
        """Both should update property values (add and remove)."""
        old_db, new_db, prop_name, video_ids = databases_with_tags

        subset = video_ids[:10]

        old_db.ops.update_property_for_videos(
            subset,
            prop_name,
            values_to_add=["new_value"],
            values_to_remove=["test_tag"],
        )
        new_db.ops.update_property_for_videos(
            subset,
            prop_name,
            values_to_add=["new_value"],
            values_to_remove=["test_tag"],
        )

        # Verify
        for vid in subset:
            old_tags = old_db.videos_tag_get(prop_name, indices=[vid])
            new_tags = new_db.videos_tag_get(prop_name, indices=[vid])
            assert "test_tag" not in old_tags[vid]
            assert "test_tag" not in new_tags[vid]
            assert "new_value" in old_tags[vid]
            assert "new_value" in new_tags[vid]


class TestValidation:
    """Test validation functions."""

    def test_validate_prop_values_string(self, mem_old_database, mem_new_database):
        """Both should validate string property values."""
        prop_name = "test_str"
        mem_old_database.prop_type_add(prop_name, "str", "", True)
        mem_new_database.prop_type_add(prop_name, "str", "", True)

        old_result = mem_old_database.ops.validate_prop_values(
            prop_name, ["value1", "value2"]
        )
        new_result = mem_new_database.ops.validate_prop_values(
            prop_name, ["value1", "value2"]
        )

        assert old_result == new_result == ["value1", "value2"]

    def test_validate_prop_values_int(self, mem_old_database, mem_new_database):
        """Both should validate integer property values."""
        prop_name = "test_int"
        mem_old_database.prop_type_add(prop_name, "int", 0, False)
        mem_new_database.prop_type_add(prop_name, "int", 0, False)

        old_result = mem_old_database.ops.validate_prop_values(prop_name, [42])
        new_result = mem_new_database.ops.validate_prop_values(prop_name, [42])

        assert old_result == new_result == [42]

    def test_validate_prop_values_enum(self, mem_old_database, mem_new_database):
        """Both should validate enum values."""
        prop_name = "test_enum"
        enum_values = ["a", "b", "c"]
        mem_old_database.prop_type_add(prop_name, "str", enum_values, False)
        mem_new_database.prop_type_add(prop_name, "str", enum_values, False)

        old_result = mem_old_database.ops.validate_prop_values(prop_name, ["a"])
        new_result = mem_new_database.ops.validate_prop_values(prop_name, ["a"])

        assert old_result == new_result == ["a"]


class TestSetPropertyForVideos:
    """Test set_property_for_videos method."""

    def test_set_property_for_videos(self, mem_old_database, mem_new_database):
        """Both should set property for multiple videos."""
        prop_name = "custom_tag"
        mem_old_database.prop_type_add(prop_name, "str", "", True)
        mem_new_database.prop_type_add(prop_name, "str", "", True)

        videos = mem_old_database.get_videos(include=["video_id"])[:20]
        video_ids = [v.video_id for v in videos]

        updates = {vid: ["custom_value"] for vid in video_ids}

        mem_old_database.ops.set_property_for_videos(prop_name, updates)
        mem_new_database.ops.set_property_for_videos(prop_name, updates)

        # Verify
        old_tags = mem_old_database.videos_tag_get(prop_name, indices=video_ids)
        new_tags = mem_new_database.videos_tag_get(prop_name, indices=video_ids)

        for vid in video_ids:
            assert old_tags[vid] == new_tags[vid] == ["custom_value"]

    def test_set_property_for_videos_merge(self, mem_old_database, mem_new_database):
        """Both should merge property values."""
        prop_name = "merge_tag"
        mem_old_database.prop_type_add(prop_name, "str", "", True)
        mem_new_database.prop_type_add(prop_name, "str", "", True)

        video_id = mem_old_database.get_videos(include=["video_id"])[0].video_id

        # Set initial
        mem_old_database.ops.set_property_for_videos(prop_name, {video_id: ["a"]})
        mem_new_database.ops.set_property_for_videos(prop_name, {video_id: ["a"]})

        # Merge
        mem_old_database.ops.set_property_for_videos(
            prop_name, {video_id: ["b"]}, merge=True
        )
        mem_new_database.ops.set_property_for_videos(
            prop_name, {video_id: ["b"]}, merge=True
        )

        old_tags = mem_old_database.videos_tag_get(prop_name, indices=[video_id])
        new_tags = mem_new_database.videos_tag_get(prop_name, indices=[video_id])

        assert sorted(old_tags[video_id]) == sorted(new_tags[video_id]) == ["a", "b"]


class TestMarkAsWatched:
    """Test mark_as_watched and mark_as_read methods."""

    def test_mark_as_watched(self, mem_old_database, mem_new_database):
        """Both should mark video as watched."""
        video_id = mem_old_database.get_videos(include=["video_id"])[0].video_id

        mem_old_database.ops.mark_as_watched(video_id)
        mem_new_database.ops.mark_as_watched(video_id)

        old_v = mem_old_database.get_videos(where={"video_id": video_id})[0]
        new_v = mem_new_database.get_videos(where={"video_id": video_id})[0]

        assert bool(old_v.watched) is bool(new_v.watched) is True
        assert old_v.date_entry_opened.time > 0
        assert new_v.date_entry_opened.time > 0

    def test_mark_as_read_toggle(self, mem_old_database, mem_new_database):
        """Both should toggle watched status."""
        video_id = mem_old_database.get_videos(include=["video_id"])[0].video_id

        # Initially not watched
        old_v = mem_old_database.get_videos(where={"video_id": video_id})[0]
        initial_watched = old_v.watched

        # Toggle
        old_result = mem_old_database.ops.mark_as_read(video_id)
        new_result = mem_new_database.ops.mark_as_read(video_id)

        assert old_result == new_result == (not initial_watched)

        # Toggle back
        old_result2 = mem_old_database.ops.mark_as_read(video_id)
        new_result2 = mem_new_database.ops.mark_as_read(video_id)

        assert old_result2 == new_result2 == initial_watched


class TestSetSimilarities:
    """Test similarity operations."""

    def test_set_similarities(self, mem_old_database, mem_new_database):
        """Both should set similarities the same way."""
        videos = mem_old_database.get_videos(include=["video_id"])[:5]
        video_ids = [v.video_id for v in videos]

        # Set similarities (all to same group)
        similarities = {vid: 100 for vid in video_ids}

        mem_old_database.ops.set_similarities(similarities)
        mem_new_database.ops.set_similarities(similarities)

        # Verify
        for vid in video_ids:
            old_v = mem_old_database.get_videos(where={"video_id": vid})[0]
            new_v = mem_new_database.get_videos(where={"video_id": vid})[0]
            assert old_v.similarity_id == new_v.similarity_id == 100

    def test_set_similarities_from_list(self, mem_old_database, mem_new_database):
        """Both should set similarities from lists."""
        videos = mem_old_database.get_videos(include=["video_id"])[:3]
        video_ids = [v.video_id for v in videos]
        sim_ids = [1, 2, 3]

        mem_old_database.ops.set_similarities_from_list(video_ids, sim_ids)
        mem_new_database.ops.set_similarities_from_list(video_ids, sim_ids)

        for vid, expected_sim in zip(video_ids, sim_ids):
            old_v = mem_old_database.get_videos(where={"video_id": vid})[0]
            new_v = mem_new_database.get_videos(where={"video_id": vid})[0]
            assert old_v.similarity_id == new_v.similarity_id == expected_sim


class TestCategoryPropertyFullWorkflow:
    """
    Full workflow test: create a property and populate it
    based on video folder structure.
    """

    def test_populate_category_from_folders(self, mem_old_database, mem_new_database):
        """Populate test_folder_category property based on folder structure."""
        prop_name = "test_folder_category"

        # Create property
        mem_old_database.prop_type_add(prop_name, "str", "", True)
        mem_new_database.prop_type_add(prop_name, "str", "", True)

        # Get all videos and extract categories
        old_videos = mem_old_database.get_videos(include=["video_id", "filename"])
        new_videos = mem_new_database.get_videos(include=["video_id", "filename"])

        # Build updates
        old_updates = {}
        for video in old_videos:
            category = get_category_from_filename(str(video.filename))
            if category != "unknown":
                old_updates[video.video_id] = [category]

        new_updates = {}
        for video in new_videos:
            category = get_category_from_filename(str(video.filename))
            if category != "unknown":
                new_updates[video.video_id] = [category]

        # Apply updates
        mem_old_database.videos_tag_set(prop_name, old_updates)
        mem_new_database.videos_tag_set(prop_name, new_updates)

        # Verify same counts
        sample_ids = list(old_updates.keys())[:100]
        old_count = mem_old_database.ops.count_property_for_videos(
            sample_ids, prop_name
        )
        new_count = mem_new_database.ops.count_property_for_videos(
            sample_ids, prop_name
        )

        assert old_count == new_count

        # Verify individual values match
        old_tags = mem_old_database.videos_tag_get(prop_name)
        new_tags = mem_new_database.videos_tag_get(prop_name)

        for vid in sample_ids:
            assert old_tags.get(vid, []) == new_tags.get(vid, [])
