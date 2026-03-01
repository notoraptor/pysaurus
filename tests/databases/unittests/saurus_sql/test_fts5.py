"""
Tests for FTS5 video_text table management in PysaurusCollection.

Verifies:
- Row lifecycle: creation/deletion of video_text rows (triggers)
- Column updates: filename, meta_title (triggers), properties (Python)
- Property operations: videos_tag_set, video_entry_set_tags, prop_type_del
- Search correctness: AND, OR, EXACT modes, case insensitivity
- camelCase splitting: camelCase terms are split into searchable pieces
"""

import pytest

from pysaurus.core.functions import string_to_pieces
from saurus.sql.pysaurus_collection import PysaurusCollection
from saurus.sql.sql_functions import pysaurus_text_to_fts
from tests.utils import get_saurus_sql_database


EXAMPLE_DB_FOLDER = pytest.importorskip("tests.conftest").EXAMPLE_DB_FOLDER


def _migrate_fts_schema(db: PysaurusCollection):
    """Upgrade video_text to the new schema (no video_id column, rowid-based)."""
    # repair_fts handles everything: drop old triggers/table, recreate, repopulate
    db.repair_fts()


@pytest.fixture
def db() -> PysaurusCollection:
    """In-memory writable copy of the example database (90 videos)."""
    collection = get_saurus_sql_database(EXAMPLE_DB_FOLDER)
    _migrate_fts_schema(collection)
    return collection


def _fts_row(db: PysaurusCollection, video_id: int):
    """Return the video_text row for a given video_id, or None."""
    return db.db.query_one(
        "SELECT rowid, filename, meta_title, properties "
        "FROM video_text WHERE rowid = ?",
        [video_id],
    )


def _fts_count(db: PysaurusCollection) -> int:
    """Return total number of rows in video_text."""
    return db.db.query_one("SELECT COUNT(*) FROM video_text")[0]


def _video_count(db: PysaurusCollection) -> int:
    """Return total number of rows in video table."""
    return db.db.query_one("SELECT COUNT(*) FROM video")[0]


def _fts_match(db: PysaurusCollection, match_expr: str) -> list[int]:
    """Raw FTS5 MATCH query, returns matching video_ids (rowids)."""
    return [
        row[0]
        for row in db.db.query_all(
            "SELECT rowid FROM video_text WHERE video_text MATCH ?", [match_expr]
        )
    ]


def _search_via_provider(
    db: PysaurusCollection, text: str, cond: str = "and"
) -> list[int]:
    """Search via provider (applies source/grouping filters)."""
    provider = db.provider
    provider.set_search(text, cond)
    return provider.get_view_indices()


def _fts_contains(properties_text: str | None, raw_value: str) -> bool:
    """Check if a raw property value is represented in FTS-processed text."""
    if properties_text is None:
        return False
    expected_pieces = string_to_pieces(raw_value.lower())
    for piece in expected_pieces:
        if piece not in properties_text.lower():
            return False
    return True


# =============================================================================
# 1. Row lifecycle
# =============================================================================


class TestFtsRowLifecycle:
    """Test that video_text rows are created/deleted with video rows."""

    def test_fts_row_count_matches_video_count(self, db):
        """Every video must have exactly one video_text row."""
        assert _fts_count(db) == _video_count(db)

    def test_video_insert_creates_fts_row(self, db):
        """INSERT INTO video must create FTS row via trigger."""
        count_before = _fts_count(db)
        db.db.modify(
            "INSERT INTO video (filename, meta_title) VALUES (?, ?)",
            ["/test/NewVideo.mp4", "New Title"],
        )
        new_id = db.db.query_one(
            "SELECT video_id FROM video WHERE filename = ?", ["/test/NewVideo.mp4"]
        )[0]
        row = _fts_row(db, new_id)
        assert row is not None
        assert row["filename"] == pysaurus_text_to_fts("/test/NewVideo.mp4")
        assert row["meta_title"] == pysaurus_text_to_fts("New Title")
        assert row["properties"] is None
        assert _fts_count(db) == count_before + 1

    def test_video_delete_removes_fts_row(self, db):
        """DELETE FROM video must remove the video_text row via trigger."""
        video_id = db.db.query_one("SELECT video_id FROM video LIMIT 1")[0]
        assert _fts_row(db, video_id) is not None

        count_before = _fts_count(db)
        db.db.modify("DELETE FROM video WHERE video_id = ?", [video_id])

        assert _fts_row(db, video_id) is None
        assert _fts_count(db) == count_before - 1

    def test_video_entry_del_removes_fts_row(self, db):
        """video_entry_del must remove the video_text row."""
        video_id = db.db.query_one("SELECT video_id FROM video LIMIT 1")[0]
        assert _fts_row(db, video_id) is not None

        db.provider.get_view_indices()  # initialize provider
        db.video_entry_del(video_id)

        assert _fts_row(db, video_id) is None
        assert _fts_count(db) == _video_count(db)

    def test_no_orphan_fts_rows_after_bulk_delete(self, db):
        """Deleting multiple videos must not leave orphan FTS rows."""
        ids = [
            row[0]
            for row in db.db.query_all(
                "SELECT video_id FROM video ORDER BY video_id LIMIT 5"
            )
        ]
        db.provider.get_view_indices()
        for vid in ids:
            db.video_entry_del(vid)

        assert _fts_count(db) == _video_count(db)
        for vid in ids:
            assert _fts_row(db, vid) is None


# =============================================================================
# 2. Column updates (filename, meta_title via triggers)
# =============================================================================


class TestFtsColumnUpdates:
    """Test that filename and meta_title updates propagate to video_text via triggers."""

    def test_filename_update_trigger(self, db):
        """UPDATE video SET filename must update video_text via trigger."""
        video_id = db.db.query_one("SELECT video_id FROM video LIMIT 1")[0]
        new_filename = "/renamed/UniqueRenamed.mp4"

        db.db.modify(
            "UPDATE video SET filename = ? WHERE video_id = ?", [new_filename, video_id]
        )
        row = _fts_row(db, video_id)
        assert row["filename"] == pysaurus_text_to_fts(new_filename)

    def test_meta_title_update_trigger(self, db):
        """UPDATE video SET meta_title must update video_text via trigger."""
        video_id = db.db.query_one("SELECT video_id FROM video LIMIT 1")[0]
        new_title = "Updated Meta Title"

        db.db.modify(
            "UPDATE video SET meta_title = ? WHERE video_id = ?", [new_title, video_id]
        )
        row = _fts_row(db, video_id)
        assert row["meta_title"] == pysaurus_text_to_fts(new_title)

    def test_filename_update_searchable(self, db):
        """After renaming, the new filename must be found via FTS MATCH."""
        video_id = db.db.query_one("SELECT video_id FROM video LIMIT 1")[0]
        unique_name = "/renamed/xyzuniquetestname.mp4"

        db.db.modify(
            "UPDATE video SET filename = ? WHERE video_id = ?", [unique_name, video_id]
        )

        assert video_id in _fts_match(db, "xyzuniquetestname*")

    def test_meta_title_update_searchable(self, db):
        """After updating meta_title, it must be found via FTS MATCH."""
        video_id = db.db.query_one("SELECT video_id FROM video LIMIT 1")[0]

        db.db.modify(
            "UPDATE video SET meta_title = ? WHERE video_id = ?",
            ["xyzuniquemetatitle", video_id],
        )

        assert video_id in _fts_match(db, "xyzuniquemetatitle*")

    def test_old_filename_not_searchable(self, db):
        """After renaming, the old filename must not match."""
        video_id = db.db.query_one("SELECT video_id FROM video LIMIT 1")[0]
        unique_old = "/test/xyzolduniquefilename.mp4"
        db.db.modify(
            "UPDATE video SET filename = ? WHERE video_id = ?", [unique_old, video_id]
        )
        assert video_id in _fts_match(db, "xyzolduniquefilename*")

        db.db.modify(
            "UPDATE video SET filename = ? WHERE video_id = ?",
            ["/completely/different/xyznewpath.mp4", video_id],
        )

        assert video_id not in _fts_match(db, "xyzolduniquefilename*")
        assert video_id in _fts_match(db, "xyznewpath*")


# =============================================================================
# 3. Properties column update (_update_fts_properties)
# =============================================================================


class TestFtsPropertiesUpdate:
    """Test that string property changes update video_text.properties."""

    def test_videos_tag_set_updates_fts(self, db):
        """videos_tag_set with string property must update FTS properties column."""
        video_id = 196
        db.videos_tag_set("category", {video_id: ["xyzuniquepropvalue"]})

        row = _fts_row(db, video_id)
        assert row["properties"] is not None
        assert "xyzuniquepropvalue" in row["properties"]

    def test_videos_tag_set_searchable_via_fts(self, db):
        """After setting a string property, it must be found via FTS MATCH."""
        video_id = 196
        db.videos_tag_set("category", {video_id: ["xyzsearchableprop"]})

        assert video_id in _fts_match(db, "xyzsearchableprop*")

    def test_videos_tag_set_searchable_via_provider(self, db):
        """After setting a string property, provider search must find it."""
        video_id = 196
        db.videos_tag_set("category", {video_id: ["xyzproviderprop"]})

        results = _search_via_provider(db, "xyzproviderprop", "and")
        assert video_id in results

    def test_videos_tag_set_all_videos(self, db):
        """videos_tag_set with None key (all videos) must update all FTS rows."""
        db.videos_tag_set("category", {None: ["xyzglobalprop"]})

        assert _fts_count(db) == _video_count(db)

        matches = _fts_match(db, "xyzglobalprop*")
        assert len(matches) == _video_count(db)

    def test_video_entry_set_tags_updates_fts(self, db):
        """video_entry_set_tags must update FTS properties."""
        video_id = 196
        db.video_entry_set_tags(video_id, {"category": ["xyzentrytagvalue"]})

        row = _fts_row(db, video_id)
        assert row["properties"] is not None
        assert "xyzentrytagvalue" in row["properties"]
        assert video_id in _fts_match(db, "xyzentrytagvalue*")

    def test_int_property_does_not_update_fts(self, db):
        """Setting a non-string property must not alter FTS properties."""
        video_id = 196
        row_before = _fts_row(db, video_id)

        db.prop_type_add("rating", "int", 0, False)
        db.video_entry_set_tags(video_id, {"rating": [5]})

        row_after = _fts_row(db, video_id)
        assert row_after["properties"] == row_before["properties"]

    def test_video_without_string_props_still_in_fts(self, db):
        """A video with no string properties must still have a video_text row."""
        video_id = 196
        db.videos_tag_set("category", {video_id: []})

        row = _fts_row(db, video_id)
        assert row is not None
        assert row["filename"] is not None

    def test_video_without_string_props_searchable_by_filename(self, db):
        """A video with no string properties must still be searchable by filename."""
        video_id = 196
        # Set a unique filename to make the test deterministic
        db.db.modify(
            "UPDATE video SET filename = ? WHERE video_id = ?",
            ["/test/xyznopropsvideo.mp4", video_id],
        )
        db.videos_tag_set("category", {video_id: []})

        assert video_id in _fts_match(db, "xyznopropsvideo*")

    def test_fts_count_stable_after_property_changes(self, db):
        """Property changes must not create or delete FTS rows."""
        count_before = _fts_count(db)

        db.videos_tag_set("category", {196: ["value1"]})
        assert _fts_count(db) == count_before

        db.videos_tag_set("category", {196: ["value2", "value3"]})
        assert _fts_count(db) == count_before

        db.videos_tag_set("category", {196: []})
        assert _fts_count(db) == count_before


# =============================================================================
# 4. prop_type_del and FTS
# =============================================================================


class TestFtsPropTypeDel:
    """Test that deleting a string property type updates FTS correctly."""

    def test_prop_type_del_clears_property_values(self, db):
        """Deleting a string property must remove its values from FTS."""
        video_id = 196
        db.videos_tag_set("category", {video_id: ["xyzwillbedeleted"]})
        assert _fts_contains(_fts_row(db, video_id)["properties"], "xyzwillbedeleted")

        db.prop_type_del("category")

        row = _fts_row(db, video_id)
        assert row is not None
        assert not _fts_contains(row["properties"], "xyzwillbedeleted")

    def test_prop_type_del_preserves_other_properties(self, db):
        """Deleting one string property must preserve others in FTS."""
        video_id = 196
        db.prop_type_add("tags", "str", "", True)
        db.videos_tag_set("tags", {video_id: ["xyzkeepthis"]})
        db.videos_tag_set("category", {video_id: ["xyzdeletethis"]})

        props_before = _fts_row(db, video_id)["properties"]
        assert _fts_contains(props_before, "xyzkeepthis")
        assert _fts_contains(props_before, "xyzdeletethis")

        db.prop_type_del("category")

        props_after = _fts_row(db, video_id)["properties"]
        assert props_after is not None
        assert _fts_contains(props_after, "xyzkeepthis")
        assert not _fts_contains(props_after, "xyzdeletethis")

    def test_prop_type_del_video_losing_all_string_props(self, db):
        """After deleting all string properties, affected videos must have
        properties=NULL but the FTS row must still exist."""
        # Delete all string property types
        str_props = db.get_prop_types(with_type=str)
        tagged_ids = set()
        for prop in str_props:
            tagged_ids.update(db.videos_tag_get(prop["name"]).keys())
        assert len(tagged_ids) > 0

        for prop in str_props:
            db.prop_type_del(prop["name"])

        for vid in tagged_ids:
            row = _fts_row(db, vid)
            assert row is not None
            assert row["properties"] is None

        assert _fts_count(db) == _video_count(db)

    def test_prop_type_del_not_searchable(self, db):
        """After deleting a property, its values must not be found via FTS."""
        video_id = 196
        db.videos_tag_set("category", {video_id: ["xyzproptodelete"]})
        assert video_id in _fts_match(db, "xyzproptodelete*")

        db.prop_type_del("category")

        assert video_id not in _fts_match(db, "xyzproptodelete*")


# =============================================================================
# 5. Search modes (AND, OR, EXACT) and case insensitivity
# =============================================================================


class TestFtsSearch:
    """Test FTS5 search with AND, OR, EXACT modes via the provider."""

    @pytest.fixture(autouse=True)
    def setup_searchable_data(self, db):
        """Set up videos with known property values for search testing."""
        self.db = db
        # Use all-lowercase terms to avoid camelCase splitting complexity
        db.videos_tag_set("category", {196: ["xyzalphaterm", "xyzbetaword"]})
        db.videos_tag_set("category", {114: ["xyzbetaword", "xyzgammaword"]})

    def test_search_and_both_terms(self):
        """AND: both terms must be present."""
        results = _search_via_provider(self.db, "xyzalphaterm xyzbetaword", "and")
        assert 196 in results
        assert 114 not in results

    def test_search_or_either_term(self):
        """OR: either term is sufficient."""
        results = _search_via_provider(self.db, "xyzalphaterm xyzgammaword", "or")
        assert 196 in results
        assert 114 in results

    def test_search_exact_single_term(self):
        """EXACT: a single term must match."""
        results = _search_via_provider(self.db, "xyzalphaterm", "exact")
        assert 196 in results
        assert 114 not in results

    def test_search_case_insensitive_and(self):
        """AND search must be case-insensitive (for whole-word terms)."""
        results_lower = _search_via_provider(self.db, "xyzalphaterm", "and")
        results_upper = _search_via_provider(self.db, "XYZALPHATERM", "and")
        assert 196 in results_lower
        assert set(results_lower) == set(results_upper)

    def test_search_case_insensitive_or(self):
        """OR search must be case-insensitive."""
        results_lower = _search_via_provider(self.db, "xyzalphaterm xyzgammaword", "or")
        results_upper = _search_via_provider(self.db, "XYZALPHATERM XYZGAMMAWORD", "or")
        assert 196 in results_lower
        assert 114 in results_lower
        assert set(results_lower) == set(results_upper)

    def test_search_case_insensitive_exact(self):
        """EXACT search must be case-insensitive."""
        results_lower = _search_via_provider(self.db, "xyzalphaterm", "exact")
        results_upper = _search_via_provider(self.db, "XYZALPHATERM", "exact")
        assert 196 in results_lower
        assert set(results_lower) == set(results_upper)

    def test_search_by_filename(self):
        """Search must find videos by filename content."""
        video_id = 196
        self.db.db.modify(
            "UPDATE video SET filename = ? WHERE video_id = ?",
            ["/test/xyzfilenameforsearch.mp4", video_id],
        )
        results = _search_via_provider(self.db, "xyzfilenameforsearch", "and")
        assert video_id in results

    def test_search_prefix_matching(self):
        """AND/OR search must support prefix matching."""
        results = _search_via_provider(self.db, "xyzalpha", "and")
        assert 196 in results

    def test_search_no_false_positives(self):
        """Search for a non-existent term must return empty."""
        results = _search_via_provider(self.db, "xyzdefinitelydoesnotexist", "and")
        assert len(results) == 0

    def test_search_after_property_removed(self):
        """After removing a property value, search must no longer match it."""
        assert 196 in _search_via_provider(self.db, "xyzalphaterm", "and")

        self.db.videos_tag_set("category", {196: ["xyzbetaword"]})
        self.db.provider.refresh()

        assert 196 not in _search_via_provider(self.db, "xyzalphaterm", "and")
        assert 196 in _search_via_provider(self.db, "xyzbetaword", "and")

    def test_search_after_property_added(self):
        """After adding a property value, search must find it."""
        assert 196 not in _search_via_provider(self.db, "xyzdeltaword", "and")

        self.db.videos_tag_set(
            "category", {196: ["xyzalphaterm", "xyzbetaword", "xyzdeltaword"]}
        )
        self.db.provider.refresh()

        assert 196 in _search_via_provider(self.db, "xyzdeltaword", "and")


# =============================================================================
# 6. Search with grouping (combined filters)
# =============================================================================


class TestFtsSearchWithGrouping:
    """Test that FTS search works correctly when combined with grouping."""

    def test_search_with_property_grouping(self, db):
        """Search + grouping by property must compose correctly."""
        db.videos_tag_set("category", {196: ["xyzgroupsearchword"]})

        provider = db.provider
        provider.set_groups(
            "category", True, sorting="count", reverse=True, allow_singletons=True
        )
        # Find the group that contains our search term
        provider.get_view_indices()
        group_def = provider.get_group_def()
        target_idx = None
        for i, g in enumerate(group_def["groups"]):
            if g["value"] == "xyzgroupsearchword":
                target_idx = i
                break
        assert target_idx is not None, "Group 'xyzgroupsearchword' not found"
        provider.set_group(target_idx)
        provider.set_search("xyzgroupsearchword", "and")
        results = provider.get_view_indices()
        assert 196 in results

    def test_search_with_attribute_grouping(self, db):
        """Search + grouping by attribute must compose correctly."""
        db.videos_tag_set("category", {196: ["xyzattrgroupword"]})

        provider = db.provider
        provider.set_groups("audio_bit_rate", allow_singletons=True)
        provider.set_search("xyzattrgroupword", "and")
        results = provider.get_view_indices()
        assert 196 in results


# =============================================================================
# 7. Exact search edge cases
# =============================================================================


class TestFtsExactSearch:
    """Test EXACT search edge cases with multi-word phrases."""

    @pytest.fixture(autouse=True)
    def setup_exact_data(self, db):
        self.db = db
        # Use lowercase terms without numbers to avoid _text_to_fts splitting
        db.videos_tag_set("category", {196: ["xyzfoo xyzbar xyzbaz"]})
        db.videos_tag_set("category", {114: ["xyzfoo xyzqux"]})

    def test_exact_adjacent_phrase(self):
        """EXACT must find adjacent word sequences."""
        results = _search_via_provider(self.db, "xyzfoo xyzbar", "exact")
        assert 196 in results
        assert 114 not in results

    def test_exact_single_word(self):
        """EXACT with a single word should match any video containing it."""
        results = _search_via_provider(self.db, "xyzfoo", "exact")
        assert 196 in results
        assert 114 in results

    def test_exact_non_adjacent_words(self):
        """EXACT must not match non-adjacent words."""
        results = _search_via_provider(self.db, "xyzfoo xyzbaz", "exact")
        # In video 196: "xyzfoo xyzbar xyzbaz" — xyzfoo and xyzbaz are NOT adjacent
        assert 196 not in results

    def test_and_vs_exact_difference(self):
        """AND finds both-terms-anywhere, EXACT requires adjacency."""
        and_results = _search_via_provider(self.db, "xyzfoo xyzbaz", "and")
        exact_results = _search_via_provider(self.db, "xyzfoo xyzbaz", "exact")
        # AND: video 196 has both terms -> match
        assert 196 in and_results
        # EXACT: xyzfoo and xyzbaz not adjacent -> no match
        assert 196 not in exact_results

    def test_or_broader_than_exact(self):
        """OR must return at least as many results as EXACT."""
        or_results = set(_search_via_provider(self.db, "xyzfoo xyzbar", "or"))
        exact_results = set(_search_via_provider(self.db, "xyzfoo xyzbar", "exact"))
        assert exact_results <= or_results

    def test_exact_partial_last_word(self):
        """EXACT with partial last word must match (prefix * on last term)."""
        # "xyzfoo xyzba" should find "xyzfoo xyzbar xyzbaz" (video 196)
        results = _search_via_provider(self.db, "xyzfoo xyzba", "exact")
        assert 196 in results

    def test_exact_partial_single_word(self):
        """EXACT with partial single word must match."""
        # "xyzfo" should find both 196 ("xyzfoo xyzbar xyzbaz") and 114 ("xyzfoo xyzqux")
        results = _search_via_provider(self.db, "xyzfo", "exact")
        assert 196 in results
        assert 114 in results

    def test_exact_dotted_filename(self):
        """EXACT search for 'AB.c' must find filename 'AB.c.mp4'."""
        video_id = 196
        self.db.db.modify(
            "UPDATE video SET filename = ? WHERE video_id = ?",
            ["/test/AB.c.mp4", video_id],
        )
        self.db.provider.refresh()
        results = _search_via_provider(self.db, "AB.c", "exact")
        assert video_id in results

    def test_exact_dotted_property(self):
        """EXACT search for 'Some.Val' must find property 'Some.Value'."""
        video_id = 196
        self.db.videos_tag_set("category", {video_id: ["Some.Value"]})
        self.db.provider.refresh()
        results = _search_via_provider(self.db, "Some.Val", "exact")
        assert video_id in results

    def test_exact_dotted_property_full(self):
        """EXACT search for 'Some.Value' must find property 'Some.Value'."""
        video_id = 196
        self.db.videos_tag_set("category", {video_id: ["Some.Value"]})
        self.db.provider.refresh()
        results = _search_via_provider(self.db, "Some.Value", "exact")
        assert video_id in results

    def test_exact_case_insensitive_dotted(self):
        """EXACT search must be case-insensitive for dotted names."""
        video_id = 196
        self.db.db.modify(
            "UPDATE video SET filename = ? WHERE video_id = ?",
            ["/test/AB.c.mp4", video_id],
        )
        self.db.provider.refresh()
        # Search with different cases
        assert video_id in _search_via_provider(self.db, "ab.c", "exact")
        assert video_id in _search_via_provider(self.db, "AB.C", "exact")
        assert video_id in _search_via_provider(self.db, "Ab.C", "exact")


# =============================================================================
# 8. FTS integrity after complex workflows
# =============================================================================


class TestFtsIntegrity:
    """Test FTS integrity after complex sequences of operations."""

    def test_multiple_property_updates_no_duplicates(self, db):
        """Multiple updates to the same video must not create duplicate FTS rows."""
        video_id = 196
        count_before = _fts_count(db)

        for i in range(5):
            db.videos_tag_set("category", {video_id: [f"iteration{chr(97 + i)}"]})

        assert _fts_count(db) == count_before

        row = _fts_row(db, video_id)
        # Last value stored was "iteratione"
        assert _fts_contains(row["properties"], "iteratione")
        assert not _fts_contains(row["properties"], "iterationa")

    def test_add_delete_property_type_cycle(self, db):
        """Adding and deleting a string property type must leave FTS intact."""
        count_before = _fts_count(db)

        db.prop_type_add("temp_prop", "str", "", True)
        db.videos_tag_set("temp_prop", {196: ["temp_value"]})
        assert _fts_count(db) == count_before

        db.prop_type_del("temp_prop")
        assert _fts_count(db) == count_before
        assert _fts_count(db) == _video_count(db)

    def test_video_entry_set_tags_then_delete(self, db):
        """Setting tags then deleting the video must clean up FTS."""
        video_id = 196
        db.video_entry_set_tags(video_id, {"category": ["xyzwillbedeleted"]})
        assert _fts_contains(_fts_row(db, video_id)["properties"], "xyzwillbedeleted")

        db.provider.get_view_indices()
        db.video_entry_del(video_id)

        assert _fts_row(db, video_id) is None
        assert _fts_count(db) == _video_count(db)

    def test_tag_set_replace_then_search(self, db):
        """Replace property value and verify search reflects the change."""
        video_id = 196
        db.videos_tag_set("category", {video_id: ["xyzoldvalue"]})
        assert video_id in _fts_match(db, "xyzoldvalue*")
        assert video_id not in _fts_match(db, "xyznewvalue*")

        db.videos_tag_set("category", {video_id: ["xyznewvalue"]})
        assert video_id not in _fts_match(db, "xyzoldvalue*")
        assert video_id in _fts_match(db, "xyznewvalue*")

    def test_batch_update_multiple_videos(self, db):
        """Batch updating properties on multiple videos must update all FTS rows."""
        ids = [
            row[0]
            for row in db.db.query_all(
                "SELECT video_id FROM video ORDER BY video_id LIMIT 10"
            )
        ]
        updates = {vid: ["xyzbatchvalue"] for vid in ids}
        db.videos_tag_set("category", updates)

        for vid in ids:
            row = _fts_row(db, vid)
            assert row["properties"] is not None
            assert "xyzbatchvalue" in row["properties"]

        matches = _fts_match(db, "xyzbatchvalue*")
        for vid in ids:
            assert vid in matches

    def test_set_tags_multiple_properties_at_once(self, db):
        """video_entry_set_tags with multiple string properties at once."""
        video_id = 196
        db.prop_type_add("tags", "str", "", True)

        db.video_entry_set_tags(
            video_id, {"category": ["xyzcatval"], "tags": ["xyztagval"]}
        )

        row = _fts_row(db, video_id)
        assert row["properties"] is not None
        assert "xyzcatval" in row["properties"]
        assert "xyztagval" in row["properties"]
        assert _fts_count(db) == _video_count(db)

    def test_provider_refresh_after_modification(self, db):
        """Provider must reflect FTS changes after refresh."""
        provider = db.provider
        provider.set_search("xyzrefreshtest", "and")
        assert len(provider.get_view_indices()) == 0

        db.videos_tag_set("category", {196: ["xyzrefreshtest"]})
        provider.refresh()
        results = provider.get_view_indices()
        assert 196 in results

        db.videos_tag_set("category", {196: []})
        provider.refresh()
        results = provider.get_view_indices()
        assert 196 not in results


# =============================================================================
# 9. camelCase splitting
# =============================================================================


class TestFtsCamelCase:
    """Test that camelCase terms are split for FTS searchability."""

    def test_camelcase_property_split_in_fts(self, db):
        """A camelCase property value must be stored as split tokens in FTS."""
        video_id = 196
        db.videos_tag_set("category", {video_id: ["xyzCamelCaseValue"]})

        row = _fts_row(db, video_id)
        # _text_to_fts("xyzCamelCaseValue") = "xyz camel case value xyzcamelcasevalue"
        assert row["properties"] is not None
        assert "xyz" in row["properties"].split()
        assert "camel" in row["properties"].split()
        assert "case" in row["properties"].split()
        assert "value" in row["properties"].split()
        assert "xyzcamelcasevalue" in row["properties"].split()

    def test_camelcase_searchable_by_parts(self, db):
        """Each part of a camelCase term must be searchable."""
        video_id = 196
        db.videos_tag_set("category", {video_id: ["xyzCamelCaseValue"]})

        assert video_id in _fts_match(db, "xyz*")
        assert video_id in _fts_match(db, "camel*")
        assert video_id in _fts_match(db, "case*")
        assert video_id in _fts_match(db, "xyzcamelcasevalue*")

    def test_camelcase_searchable_via_provider(self, db):
        """Provider must find camelCase terms by their constituent parts."""
        video_id = 196
        db.videos_tag_set("category", {video_id: ["xyzMySpecialTag"]})

        assert video_id in _search_via_provider(db, "xyzMySpecialTag", "and")
        assert video_id in _search_via_provider(db, "special", "and")
        assert video_id in _search_via_provider(db, "xyzMySpecialTag", "exact")

    def test_camelcase_filename_split(self, db):
        """camelCase in filenames must be split for search via trigger."""
        video_id = 196
        db.db.modify(
            "UPDATE video SET filename = ? WHERE video_id = ?",
            ["/test/xyzMyTestFile.mp4", video_id],
        )

        assert video_id in _fts_match(db, "test*")
        assert video_id in _fts_match(db, "file*")

    def test_repair_fts_applies_camelcase_splitting(self, db):
        """repair_fts must apply camelCase splitting to all columns."""
        video_id = 196
        # Set raw (non-split) data directly
        db.db.modify(
            "UPDATE video_text SET filename = 'xyzCamelTest.mp4' WHERE rowid = ?",
            [video_id],
        )
        # Before repair, the raw text is not split
        assert video_id not in _fts_match(db, "camel*")

        db.repair_fts()

        # After repair, camelCase should be split
        row = _fts_row(db, video_id)
        assert row is not None
        # filename in video table still has original, but FTS has split version
