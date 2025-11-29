"""
Tests to compare JSON database with NewSQL and Saurus SQL database implementations.

These tests ensure that all database implementations return consistent
results for all read operations defined in AbstractDatabase.

The JSON database (fake_old_database) is the reference implementation.
"""

import pytest

from pysaurus.database.abstract_database import AbstractDatabase


@pytest.fixture(params=["newsql", "saurus_sql"])
def test_database(request, fake_new_database, fake_saurus_database) -> AbstractDatabase:
    """Parametrized fixture that yields each database implementation to test."""
    if request.param == "newsql":
        return fake_new_database
    else:
        return fake_saurus_database


class TestDatabaseComparison:
    """Compare JSON database with other implementations."""

    # =========================================================================
    # Basic info
    # =========================================================================

    def test_get_name(self, fake_old_database, test_database):
        """Both databases should have the same name."""
        assert fake_old_database.get_name() == test_database.get_name()

    def test_get_folders(self, fake_old_database, test_database):
        """Both databases should return the same folders."""
        old_folders = sorted(str(f) for f in fake_old_database.get_folders())
        new_folders = sorted(str(f) for f in test_database.get_folders())
        assert old_folders == new_folders

    # =========================================================================
    # get_videos - basic
    # =========================================================================

    def test_get_videos_count(self, fake_old_database, test_database):
        """Both databases should have the same number of videos."""
        old_videos = fake_old_database.get_videos()
        new_videos = test_database.get_videos()
        assert len(old_videos) == len(new_videos)

    def test_get_videos_ids(self, fake_old_database, test_database):
        """Both databases should have the same video IDs."""
        old_ids = sorted(v.video_id for v in fake_old_database.get_videos())
        new_ids = sorted(v.video_id for v in test_database.get_videos())
        assert old_ids == new_ids

    def test_get_videos_filenames(self, fake_old_database, test_database):
        """Both databases should have the same filenames."""
        old_filenames = sorted(str(v.filename) for v in fake_old_database.get_videos())
        new_filenames = sorted(str(v.filename) for v in test_database.get_videos())
        assert old_filenames == new_filenames

    # =========================================================================
    # get_videos - with include parameter
    # =========================================================================

    def test_get_videos_include_video_id(self, fake_old_database, test_database):
        """Both should return video_id when included."""
        old_videos = fake_old_database.get_videos(include=["video_id"])
        new_videos = test_database.get_videos(include=["video_id"])
        old_ids = sorted(v.video_id for v in old_videos)
        new_ids = sorted(v.video_id for v in new_videos)
        assert old_ids == new_ids

    def test_get_videos_include_filename(self, fake_old_database, test_database):
        """Both should return filename when included."""
        old_videos = fake_old_database.get_videos(include=["filename"])
        new_videos = test_database.get_videos(include=["filename"])
        old_filenames = sorted(str(v.filename) for v in old_videos)
        new_filenames = sorted(str(v.filename) for v in new_videos)
        assert old_filenames == new_filenames

    def test_get_videos_include_multiple(self, fake_old_database, test_database):
        """Both should handle multiple includes."""
        old_videos = fake_old_database.get_videos(
            include=["video_id", "filename", "file_size"]
        )
        new_videos = test_database.get_videos(
            include=["video_id", "filename", "file_size"]
        )
        old_data = sorted(
            (v.video_id, str(v.filename), v.file_size) for v in old_videos
        )
        new_data = sorted(
            (v.video_id, str(v.filename), v.file_size) for v in new_videos
        )
        assert old_data == new_data

    # =========================================================================
    # get_videos - with where parameter
    # =========================================================================

    def test_get_videos_where_video_id(self, fake_old_database, test_database):
        """Both should filter by video_id."""
        # Get a sample video_id from old database
        all_old = fake_old_database.get_videos(include=["video_id"])
        if all_old:
            sample_id = all_old[0].video_id
            old_videos = fake_old_database.get_videos(where={"video_id": sample_id})
            new_videos = test_database.get_videos(where={"video_id": sample_id})
            assert len(old_videos) == len(new_videos) == 1
            assert old_videos[0].video_id == new_videos[0].video_id

    def test_get_videos_where_readable(self, fake_old_database, test_database):
        """Both should filter by readable flag."""
        old_readable = fake_old_database.get_videos(where={"readable": True})
        new_readable = test_database.get_videos(where={"readable": True})
        assert len(old_readable) == len(new_readable)

        old_unreadable = fake_old_database.get_videos(where={"unreadable": True})
        new_unreadable = test_database.get_videos(where={"unreadable": True})
        assert len(old_unreadable) == len(new_unreadable)

    def test_get_videos_where_found(self, fake_old_database, test_database):
        """Both should filter by found flag."""
        old_found = fake_old_database.get_videos(where={"found": True})
        new_found = test_database.get_videos(where={"found": True})
        assert len(old_found) == len(new_found)

        old_not_found = fake_old_database.get_videos(where={"not_found": True})
        new_not_found = test_database.get_videos(where={"not_found": True})
        assert len(old_not_found) == len(new_not_found)

    def test_get_videos_where_with_thumbnails(self, fake_old_database, test_database):
        """Both should filter by thumbnail presence."""
        old_with = fake_old_database.get_videos(where={"with_thumbnails": True})
        new_with = test_database.get_videos(where={"with_thumbnails": True})
        assert len(old_with) == len(new_with)

        old_without = fake_old_database.get_videos(where={"without_thumbnails": True})
        new_without = test_database.get_videos(where={"without_thumbnails": True})
        assert len(old_without) == len(new_without)

    # =========================================================================
    # Video attributes comparison
    # =========================================================================

    def test_video_attributes_match(self, fake_old_database, test_database):
        """All video attributes should match between databases."""
        old_videos = {v.video_id: v for v in fake_old_database.get_videos()}
        new_videos = {v.video_id: v for v in test_database.get_videos()}

        # Test a sample of videos (first 100)
        sample_ids = sorted(old_videos.keys())[:100]

        attributes = [
            "video_id",
            "filename",
            "file_size",
            "duration",
            "width",
            "height",
            "readable",
            "unreadable",
            "audio_codec",
            "video_codec",
            "container_format",
            "frame_rate_num",
            "frame_rate_den",
            "meta_title",
            "title",
            "file_title",
            "extension",
            "similarity_id",
            "watched",
            "date_entry_modified",
            "date_entry_opened",
        ]

        # Attributes that should be treated as booleans
        bool_attributes = {"readable", "unreadable", "watched"}

        def normalize_value(val, attr_name):
            """Normalize value for comparison (handles int/float/bool differences)."""
            if val is None:
                return None
            # Convert 0/1 to bool for boolean attributes
            if attr_name in bool_attributes and isinstance(val, int):
                return bool(val)
            if isinstance(val, bool):
                return val
            if isinstance(val, float) and val.is_integer():
                return int(val)
            return val

        for video_id in sample_ids:
            old_v = old_videos[video_id]
            new_v = new_videos[video_id]
            for attr in attributes:
                old_val = normalize_value(getattr(old_v, attr, None), attr)
                new_val = normalize_value(getattr(new_v, attr, None), attr)
                # Convert to comparable types
                old_val = str(old_val) if old_val is not None else None
                new_val = str(new_val) if new_val is not None else None
                assert old_val == new_val, (
                    f"Mismatch for video {video_id}, attribute {attr}: "
                    f"old={old_val}, new={new_val}"
                )

    # =========================================================================
    # count_videos
    # =========================================================================

    def test_count_videos_total(self, fake_old_database, test_database):
        """Both should return the same total count."""
        assert fake_old_database.ops.count_videos() == test_database.ops.count_videos()

    def test_count_videos_readable(self, fake_old_database, test_database):
        """Both should return the same readable count."""
        assert fake_old_database.ops.count_videos(
            "readable"
        ) == test_database.ops.count_videos("readable")

    def test_count_videos_with_thumbnails(self, fake_old_database, test_database):
        """Both should return the same count with thumbnails."""
        assert fake_old_database.ops.count_videos(
            "with_thumbnails"
        ) == test_database.ops.count_videos("with_thumbnails")

    # =========================================================================
    # has_video
    # =========================================================================

    def test_has_video_by_id(self, fake_old_database, test_database):
        """Both should agree on video existence by ID."""
        old_videos = fake_old_database.get_videos(include=["video_id"])
        sample_ids = [v.video_id for v in old_videos[:10]]

        for video_id in sample_ids:
            assert fake_old_database.ops.has_video(
                video_id=video_id
            ) == test_database.ops.has_video(video_id=video_id)

        # Test non-existent ID
        max_id = max(v.video_id for v in old_videos) if old_videos else 0
        assert fake_old_database.ops.has_video(
            video_id=max_id + 9999
        ) == test_database.ops.has_video(video_id=max_id + 9999)

    def test_has_video_by_filename(self, fake_old_database, test_database):
        """Both should agree on video existence by filename."""
        old_videos = fake_old_database.get_videos(include=["filename"])
        sample_filenames = [v.filename for v in old_videos[:10]]

        for filename in sample_filenames:
            assert fake_old_database.ops.has_video(
                filename=filename
            ) == test_database.ops.has_video(filename=filename)

    # =========================================================================
    # get_video_filename
    # =========================================================================

    def test_get_video_filename(self, fake_old_database, test_database):
        """Both should return the same filename for a given video ID."""
        old_videos = fake_old_database.get_videos(include=["video_id"])
        sample_ids = [v.video_id for v in old_videos[:10]]

        for video_id in sample_ids:
            old_filename = fake_old_database.ops.get_video_filename(video_id)
            new_filename = test_database.ops.get_video_filename(video_id)
            assert str(old_filename) == str(new_filename)

    # =========================================================================
    # get_prop_types
    # =========================================================================

    def test_get_prop_types_all(self, fake_old_database, test_database):
        """Both should return the same property types."""
        old_props = fake_old_database.get_prop_types()
        new_props = test_database.get_prop_types()

        old_names = sorted(p["name"] for p in old_props)
        new_names = sorted(p["name"] for p in new_props)
        assert old_names == new_names

    def test_get_prop_types_by_name(self, fake_old_database, test_database):
        """Both should return the same property type by name."""
        old_props = fake_old_database.get_prop_types()
        for prop in old_props:
            name = prop["name"]
            old_by_name = fake_old_database.get_prop_types(name=name)
            new_by_name = test_database.get_prop_types(name=name)
            assert len(old_by_name) == len(new_by_name)

    # =========================================================================
    # videos_get_terms
    # =========================================================================

    def test_videos_get_terms_keys(self, fake_old_database, test_database):
        """Both should return terms for the same video IDs."""
        old_terms = fake_old_database.videos_get_terms()
        new_terms = test_database.videos_get_terms()

        assert sorted(old_terms.keys()) == sorted(new_terms.keys())

    def test_videos_get_terms_values(self, fake_old_database, test_database):
        """Both should return similar terms for each video."""
        old_terms = fake_old_database.videos_get_terms()
        new_terms = test_database.videos_get_terms()

        # Test a sample of videos
        sample_ids = sorted(old_terms.keys())[:50]

        for video_id in sample_ids:
            old_set = set(old_terms[video_id])
            new_set = set(new_terms[video_id])
            # Terms should be the same (order may differ)
            assert old_set == new_set, (
                f"Terms mismatch for video {video_id}: old={old_set}, new={new_set}"
            )

    # =========================================================================
    # videos_tag_get
    # =========================================================================

    def test_videos_tag_get(self, fake_old_database, test_database):
        """Both should return the same property values."""
        old_props = fake_old_database.get_prop_types()

        for prop in old_props:
            name = prop["name"]
            old_tags = fake_old_database.videos_tag_get(name)
            new_tags = test_database.videos_tag_get(name)

            # Same keys
            assert sorted(old_tags.keys()) == sorted(new_tags.keys()), (
                f"Keys mismatch for property {name}"
            )

            # Same values
            for video_id in old_tags:
                old_values = sorted(str(v) for v in old_tags[video_id])
                new_values = sorted(str(v) for v in new_tags[video_id])
                assert old_values == new_values, (
                    f"Values mismatch for property {name}, video {video_id}: "
                    f"old={old_values}, new={new_values}"
                )

    def test_videos_tag_get_with_indices(self, fake_old_database, test_database):
        """Both should return the same values when filtering by indices."""
        old_props = fake_old_database.get_prop_types()
        if not old_props:
            pytest.skip("No properties defined")

        # Get sample video IDs
        old_videos = fake_old_database.get_videos(include=["video_id"])
        sample_ids = [v.video_id for v in old_videos[:20]]

        for prop in old_props:
            name = prop["name"]
            old_tags = fake_old_database.videos_tag_get(name, indices=sample_ids)
            new_tags = test_database.videos_tag_get(name, indices=sample_ids)

            assert sorted(old_tags.keys()) == sorted(new_tags.keys())

    # =========================================================================
    # videos_get_moves
    # =========================================================================

    def test_videos_get_moves(self, fake_old_database, test_database):
        """Both should return the same potential moves."""
        old_moves = list(fake_old_database.videos_get_moves())
        new_moves = list(test_database.videos_get_moves())

        # Same number of videos with moves
        assert len(old_moves) == len(new_moves)

        # Same video IDs
        old_move_ids = sorted(m[0] for m in old_moves)
        new_move_ids = sorted(m[0] for m in new_moves)
        assert old_move_ids == new_move_ids

    def test_get_unique_moves(self, fake_old_database, test_database):
        """Both should return the same unique moves."""
        old_unique = fake_old_database.algos.get_unique_moves()
        new_unique = test_database.algos.get_unique_moves()

        assert sorted(old_unique) == sorted(new_unique)

    # =========================================================================
    # Thumbnails
    # =========================================================================

    def test_thumbnail_presence(self, fake_old_database, test_database):
        """Both should report the same thumbnail presence for each video."""
        old_videos = fake_old_database.get_videos()
        new_videos_map = {v.video_id: v for v in test_database.get_videos()}

        # Test a sample of videos
        sample = old_videos[:100]

        for old_v in sample:
            new_v = new_videos_map[old_v.video_id]
            assert old_v.with_thumbnails == new_v.with_thumbnails, (
                f"Thumbnail presence mismatch for video {old_v.video_id}: "
                f"old={old_v.with_thumbnails}, new={new_v.with_thumbnails}"
            )

    def test_thumbnail_data(self, fake_old_database, test_database):
        """Both should return the same thumbnail data."""
        old_videos = fake_old_database.get_videos(where={"with_thumbnails": True})
        new_videos_map = {v.video_id: v for v in test_database.get_videos()}

        # Test a sample of videos with thumbnails
        sample = old_videos[:20]

        for old_v in sample:
            new_v = new_videos_map[old_v.video_id]
            old_thumb = old_v.thumbnail
            new_thumb = new_v.thumbnail

            if old_thumb is None:
                assert new_thumb is None
            else:
                assert new_thumb is not None
                assert len(old_thumb) == len(new_thumb), (
                    f"Thumbnail size mismatch for video {old_v.video_id}"
                )
                assert old_thumb == new_thumb, (
                    f"Thumbnail data mismatch for video {old_v.video_id}"
                )


class TestDatabaseComparisonEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_where_clause(self, fake_old_database, test_database):
        """Empty where clause should return all videos."""
        old_all = fake_old_database.get_videos(where={})
        new_all = test_database.get_videos(where={})
        assert len(old_all) == len(new_all)

    def test_multiple_where_conditions(self, fake_old_database, test_database):
        """Multiple where conditions should work the same."""
        old_videos = fake_old_database.get_videos(
            where={"readable": True, "found": True}
        )
        new_videos = test_database.get_videos(where={"readable": True, "found": True})
        assert len(old_videos) == len(new_videos)

    def test_get_videos_list_of_ids(self, fake_old_database, test_database):
        """Both should handle a list of video IDs in where clause."""
        all_old = fake_old_database.get_videos(include=["video_id"])
        sample_ids = [v.video_id for v in all_old[:5]]

        old_videos = fake_old_database.get_videos(where={"video_id": sample_ids})
        new_videos = test_database.get_videos(where={"video_id": sample_ids})

        assert len(old_videos) == len(new_videos) == len(sample_ids)
        assert sorted(v.video_id for v in old_videos) == sorted(
            v.video_id for v in new_videos
        )
