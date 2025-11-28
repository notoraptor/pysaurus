"""
Test video move detection in NewSqlDatabase.

A move is detected when:
- A video is "not found" (R.f = false)
- Another video with the same (file_size, duration, duration_time_base) is "found" (R.f = true)

When grouping by "move_id", each group contains:
- One or more not_found videos (the "moved" files)
- One or more found videos (potential destinations)
"""

import json
from pathlib import Path

import pytest

from pysaurus.database.jsdb.db_video_attribute import PotentialMoveAttribute
from pysaurus.database.newsql.newsql_database import SqlVideo
from pysaurus.database.newsql.sql_database import SqlDatabase


class MockNewSqlDatabase:
    """
    Mock database that mimics NewSqlDatabase behavior for testing moves.

    Uses in-memory SQLite and provides the interface expected by PotentialMoveAttribute.
    """

    def __init__(self, videos: list[dict], prop_types: list[dict] = None):
        self._sql = SqlDatabase(":memory:")
        self._sql.init_schema()
        self._folders = set()

        # Add prop_types
        for pt in prop_types or []:
            name = pt.get("n") or pt.get("name")
            definition = pt.get("d") or pt.get("definition")
            multiple = pt.get("m", False) or pt.get("multiple", False)
            self._sql.set_prop_type(name, definition, multiple)

        # Add videos
        for video_dict in videos:
            video_id = video_dict.get("j") or video_dict.get("video_id", 0)
            filename = video_dict.get("f") or video_dict.get("filename", "")
            self._sql.insert_video(video_id, filename, video_dict)

        # Initialize moves_attribute like JsonDatabase does
        self.moves_attribute = PotentialMoveAttribute(self)

    def close(self):
        self._sql.close()

    def get_videos(
        self, *, include=None, with_moves=False, where=None
    ) -> list[SqlVideo]:
        """Get videos matching criteria, compatible with PotentialMoveAttribute."""
        where = dict(where) if where else {}

        # Get all videos from SQL
        videos = self._sql.get_all_videos()

        # Wrap as SqlVideo
        results = [
            SqlVideo(v["video_id"], v["filename"], v["data"], self) for v in videos
        ]

        # Apply filters
        for key, value in where.items():
            results = [v for v in results if getattr(v, key, None) == value]

        return results

    def has_thumbnail(self, filename):
        return False

    def get_thumbnail_blob(self, filename):
        return None

    def get_thumbnail_base64(self, filename):
        return ""

    def _is_discarded(self, filename):
        return False

    def videos_get_moves(self):
        """Get detected moves - delegates to PotentialMoveAttribute."""
        return self.moves_attribute.get_moves()


@pytest.fixture
def sample_data():
    """Load sample data from test file."""
    test_file = Path(__file__).parent / "newsql_test_samples.json"
    with open(test_file, "r", encoding="utf-8") as f:
        return json.load(f)


def test_move_detection_via_database(sample_data):
    """
    Test that moves are detected through the database interface.

    This tests the full flow: database -> PotentialMoveAttribute -> moves
    """
    videos = sample_data["videos"]
    prop_types = sample_data["prop_types"]

    db = MockNewSqlDatabase(videos, prop_types)

    # Get moves via database method (same as JsonDatabase.videos_get_moves)
    moves = dict(db.videos_get_moves())

    # We should detect one move:
    # - video_id 9999 (old Digimon location, not found) -> video_id 0 (new location, found)
    assert len(moves) == 1
    assert 9999 in moves

    destinations = moves[9999]
    assert len(destinations) == 1
    assert destinations[0]["video_id"] == 0
    assert "Digimon Tamers 2021" in destinations[0]["filename"]

    db.close()


def test_move_id_and_moves_properties(sample_data):
    """
    Test that move_id and moves properties work on SqlVideo via moves_attribute.
    """
    videos = sample_data["videos"]
    prop_types = sample_data["prop_types"]

    db = MockNewSqlDatabase(videos, prop_types)

    # Get the not_found video (9999) and found video (0)
    all_videos = db.get_videos()
    video_9999 = next(v for v in all_videos if v.video_id == 9999)
    video_0 = next(v for v in all_videos if v.video_id == 0)

    # Check move_id - both should be in same group
    move_id_9999, moves_9999 = db.moves_attribute(video_9999.video_id)
    move_id_0, moves_0 = db.moves_attribute(video_0.video_id)

    # Both videos should have the same move_id (group identifier)
    assert move_id_9999 is not None
    assert move_id_0 is not None
    assert move_id_9999 == move_id_0

    # The not_found video (9999) should have moves (destinations)
    assert len(moves_9999) == 1
    assert moves_9999[0]["video_id"] == 0

    # The found video (0) should NOT have moves (it's a destination, not a source)
    assert len(moves_0) == 0

    db.close()


def test_no_move_when_no_found_match(sample_data):
    """Test that no move is detected when there's no matching found video."""
    # Use only the first 4 videos (none have a found match with same size/duration)
    videos = sample_data["videos"][:4]

    db = MockNewSqlDatabase(videos)

    moves = dict(db.videos_get_moves())

    # No moves should be detected
    assert len(moves) == 0

    db.close()


def test_multiple_possible_destinations():
    """Test move detection when multiple files match the same (size, duration)."""
    # Create two found videos with same size/duration, and one not_found
    videos = [
        {
            "j": 1,
            "f": "C:\\videos\\movie_copy1.mkv",
            "s": 100000000,
            "d": 3600000000,
            "t": 1000000,
            "U": False,
            "e": [],
            "R": {"f": True, "m": 1000.0, "d": 0, "s": 100000000},
        },
        {
            "j": 2,
            "f": "D:\\backup\\movie_copy2.mkv",
            "s": 100000000,
            "d": 3600000000,
            "t": 1000000,
            "U": False,
            "e": [],
            "R": {"f": True, "m": 1000.0, "d": 1, "s": 100000000},
        },
        {
            "j": 3,
            "f": "E:\\old\\movie_original.mkv",
            "s": 100000000,
            "d": 3600000000,
            "t": 1000000,
            "U": False,
            "e": [],
            "R": {"f": False, "m": 1000.0, "d": 2, "s": 100000000},
        },
    ]

    db = MockNewSqlDatabase(videos)

    moves = dict(db.videos_get_moves())

    # One move detected (video 3 is not_found)
    assert len(moves) == 1
    assert 3 in moves

    # Two possible destinations
    destinations = moves[3]
    assert len(destinations) == 2
    dest_ids = {d["video_id"] for d in destinations}
    assert dest_ids == {1, 2}

    # Check move_id grouping - all 3 should have same move_id
    move_id_1, _ = db.moves_attribute(1)
    move_id_2, _ = db.moves_attribute(2)
    move_id_3, _ = db.moves_attribute(3)

    assert move_id_1 == move_id_2 == move_id_3
    assert move_id_1 is not None

    db.close()


def test_unreadable_videos_excluded_from_moves(sample_data):
    """Test that unreadable videos are not considered for move detection."""
    videos = sample_data["videos"]

    db = MockNewSqlDatabase(videos)

    # The unreadable videos (8643, 8644) should not appear in moves
    # even though they are not_found
    moves = dict(db.videos_get_moves())

    # Only video 9999 should be in moves (readable and not_found)
    assert 8643 not in moves
    assert 8644 not in moves

    db.close()


if __name__ == "__main__":
    # Quick test without pytest
    test_file = Path(__file__).parent / "newsql_test_samples.json"
    with open(test_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("Testing move detection via database...")
    print("=" * 70)

    videos = data["videos"]
    print(f"Loaded {len(videos)} videos")

    # Show video summary
    for v in videos:
        vid = v.get("j", 0)
        fn = v.get("f", "")
        fn_short = f"...{fn[-40:]}" if len(fn) > 40 else fn
        runtime = v.get("R", {})
        found = runtime.get("f", True) if isinstance(runtime, dict) else False
        unreadable = v.get("U", False)
        size = v.get("s", 0)
        duration = v.get("d", 0)
        status = "unreadable" if unreadable else ("found" if found else "NOT FOUND")
        print(f"  [{vid:5}] {status:12} size={size:12} duration={duration:12}")
        print(f"          {fn_short}")

    print()

    db = MockNewSqlDatabase(videos, data.get("prop_types", []))

    # Get moves
    moves = dict(db.videos_get_moves())

    print(f"Detected moves: {len(moves)}")
    for video_id, destinations in moves.items():
        move_id, _ = db.moves_attribute(video_id)
        print(f"\n  Video {video_id} (move_id={move_id!r}):")
        print("  Can be moved to:")
        for dest in destinations:
            print(f"    -> [{dest['video_id']}] {dest['filename']}")

    print()

    # Show all videos with their move_id
    print("All videos with move_id:")
    for v in db.get_videos():
        move_id, moves_list = db.moves_attribute(v.video_id)
        if move_id:
            status = f"moves={len(moves_list)}" if moves_list else "destination"
            print(f"  [{v.video_id:5}] move_id={move_id!r} ({status})")

    db.close()

    print("\n" + "=" * 70)
    print("Done!")
