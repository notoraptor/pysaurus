"""
Test that SqlVideo returns the same values as LazyVideo for the same data.
"""

import json
from pathlib import Path

import pytest
from pysaurus.database.jsdb.jsdbvideo.lazy_video import LazyVideo
from pysaurus.database.newsql.newsql_database import SqlVideo

# Properties to compare (from VIDEO_SCHEMA)
# Note: Some properties require database access in LazyVideo, so we skip those
PROPERTIES_TO_TEST = [
    "video_id",
    "filename",
    "file_size",
    "errors",
    "unreadable",
    "readable",
    "meta_title",
    "properties",
    "similarity_id",
    "watched",
    "date_entry_modified",
    "date_entry_opened",
    "title",
    "file_title",
    # Runtime
    "found",
    "not_found",
    "mtime",
    "driver_id",
    # Video technical
    "duration",
    "duration_time_base",
    "width",
    "height",
    "audio_codec",
    "video_codec",
    "container_format",
    "frame_rate_num",
    "frame_rate_den",
    "audio_bit_rate",
    "sample_rate",
    "channels",
    "audio_bits",
    "audio_codec_description",
    "video_codec_description",
    "bit_depth",
    "device_name",
    "audio_languages",
    "subtitle_languages",
    # Derived (these work without database)
    "extension",
    "disk",
]


class MockDatabase:
    """Mock database for SqlVideo that doesn't need real SQL connection."""

    def __init__(self, folders=None):
        self._folders = set(folders or [])
        self._thumbnails = set()

    def has_thumbnail(self, filename):
        return str(filename) in self._thumbnails

    def get_thumbnail_blob(self, filename):
        return None

    def get_thumbnail_base64(self, filename):
        return ""

    def _is_discarded(self, filename):
        for folder in self._folders:
            if str(filename).startswith(str(folder)):
                return False
        return True


@pytest.fixture
def sample_videos():
    """Load sample videos from test file."""
    test_file = Path(__file__).parent / "newsql_test_samples.json"
    with open(test_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["videos"]


def normalize_value(value):
    """Normalize values for comparison."""
    if hasattr(value, "path"):
        # AbsolutePath -> string
        return value.path
    if hasattr(value, "time"):
        # Date -> float
        return value.time
    if hasattr(value, "value"):
        # Text -> string
        return value.value
    if isinstance(value, set):
        # set -> sorted list
        return sorted(value)
    if isinstance(value, list):
        # list -> sorted list for comparison
        return sorted(value) if value else value
    return value


def test_sqlvideo_matches_lazyvideo(sample_videos):
    """Test that SqlVideo returns same values as LazyVideo."""
    mock_db = MockDatabase()

    for video_dict in sample_videos:
        # Create LazyVideo (original implementation)
        # LazyVideo signature: (database, short_dict, discarded=False)
        lazy_video = LazyVideo(None, video_dict, discarded=False)

        # Create SqlVideo (new implementation)
        video_id = video_dict.get("j") or video_dict.get("video_id", 0)
        filename = video_dict.get("f") or video_dict.get("filename", "")
        sql_video = SqlVideo(video_id, filename, video_dict, mock_db)

        # Compare all properties
        mismatches = []
        for prop in PROPERTIES_TO_TEST:
            try:
                lazy_value = normalize_value(getattr(lazy_video, prop, "N/A"))
                sql_value = normalize_value(getattr(sql_video, prop, "N/A"))

                if lazy_value != sql_value:
                    mismatches.append(
                        f"  {prop}: LazyVideo={lazy_value!r}, SqlVideo={sql_value!r}"
                    )
            except Exception as e:
                mismatches.append(f"  {prop}: ERROR - {e}")

        if mismatches:
            fn_short = filename[-60:] if len(filename) > 60 else filename
            pytest.fail(
                f"Mismatches for video ...{fn_short}:\n" + "\n".join(mismatches)
            )


def test_sqlvideo_individual_properties(sample_videos):
    """Test individual properties in detail."""
    mock_db = MockDatabase()

    for video_dict in sample_videos:
        video_id = video_dict.get("j") or video_dict.get("video_id", 0)
        filename = video_dict.get("f") or video_dict.get("filename", "")
        sql_video = SqlVideo(video_id, filename, video_dict, mock_db)
        lazy_video = LazyVideo(None, video_dict, discarded=False)

        # Test specific properties
        assert sql_video.video_id == lazy_video.video_id
        assert sql_video.filename.path == lazy_video.filename.path
        assert sql_video.file_size == lazy_video.file_size
        assert sql_video.unreadable == lazy_video.unreadable
        assert sql_video.readable == lazy_video.readable

        if not sql_video.unreadable:
            # Only readable videos have these properties
            assert sql_video.duration == lazy_video.duration
            assert sql_video.width == lazy_video.width
            assert sql_video.height == lazy_video.height
            assert sql_video.audio_codec == lazy_video.audio_codec
            assert sql_video.video_codec == lazy_video.video_codec


if __name__ == "__main__":
    # Run quick test without pytest
    test_file = Path(__file__).parent / "newsql_test_samples.json"
    with open(test_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    sample_videos = data["videos"]
    mock_db = MockDatabase()

    print("Comparing SqlVideo vs LazyVideo...")
    print("=" * 70)

    for i, video_dict in enumerate(sample_videos):
        video_id = video_dict.get("j") or video_dict.get("video_id", 0)
        filename = video_dict.get("f") or video_dict.get("filename", "")
        fn_short = f"...{filename[-50:]}" if len(filename) > 50 else filename

        print(f"\nVideo {i + 1}: {fn_short}")
        print(f"  unreadable: {video_dict.get('U', False)}")

        lazy_video = LazyVideo(None, video_dict, discarded=False)
        sql_video = SqlVideo(video_id, filename, video_dict, mock_db)

        mismatches = []
        matches = 0

        for prop in PROPERTIES_TO_TEST:
            try:
                lazy_value = normalize_value(getattr(lazy_video, prop, "N/A"))
                sql_value = normalize_value(getattr(sql_video, prop, "N/A"))

                if lazy_value != sql_value:
                    mismatches.append((prop, lazy_value, sql_value))
                else:
                    matches += 1
            except Exception as e:
                mismatches.append((prop, "ERROR", str(e)))

        print(f"  OK: {matches} properties match")

        if mismatches:
            print(f"  MISMATCH: {len(mismatches)} differences:")
            for prop, lazy_val, sql_val in mismatches:
                print(f"    {prop}:")
                print(f"      LazyVideo: {lazy_val!r}")
                print(f"      SqlVideo:  {sql_val!r}")

    print("\n" + "=" * 70)
    print("Done!")
