"""
Experimental test to check if pyfakefs works with the JSON database.

CONCLUSION: pyfakefs DOES NOT WORK for this use case.

The JSON database uses:
- JSON files for data
- Pickle files for indexes
- SQLite for thumbnails
- multiprocessing.Manager() for notifications

ISSUES ENCOUNTERED:

1. RESOLVED: Package files needed by pysaurus
   - Solution: Application() no longer loads language files in __init__

2. RESOLVED: External SQL file for thumbnails
   - Solution: SQL script embedded directly in the Python code

3. BLOCKING: multiprocessing.Manager() incompatible with pyfakefs
   - Error: OSError: [Errno 9] Bad file descriptor
   - Cause: pyfakefs cannot simulate the low-level file descriptors
     used by multiprocessing for inter-process communication
   - Location: pysaurus/core/informer.py:39 creates a Manager()

4. BLOCKING: SQLite low-level operations (fcntl, flock)
   - Even if multiprocessing is resolved, SQLite uses system calls
     that pyfakefs does not fully simulate

RECOMMENDATION:
- For mem_old_database: Continue with shutil.copytree() + tmp_path
- For mem_saurus_database: Continue with in-memory SQLite copy

These tests are kept as documentation of the attempt to use pyfakefs
and the reasons for its failure.
"""

import pytest

from pysaurus.application.application import Application
from tests.utils import TEST_HOME_DIR


@pytest.mark.skip(reason="Experimental test for pyfakefs compatibility")
def test_pyfakefs_simple_read(fs):
    """Test simple: lire la base JSON avec pyfakefs."""
    # Copy real filesystem to fake filesystem
    fs.add_real_directory(TEST_HOME_DIR, read_only=False)

    # Try to load the database
    app = Application(home_dir=TEST_HOME_DIR)
    db = app.open_database_from_name("test_database")

    # Simple read operation
    videos = db.get_videos(include=["video_id", "filename"])
    assert len(videos) > 0
    print(f"[OK] Successfully read {len(videos)} videos with pyfakefs")


@pytest.mark.skip(reason="Experimental test for pyfakefs compatibility")
def test_pyfakefs_sqlite_thumbnails(fs):
    """Test SQLite operations (thumbnails) with pyfakefs."""
    fs.add_real_directory(TEST_HOME_DIR, read_only=False)

    app = Application(home_dir=TEST_HOME_DIR)
    db = app.open_database_from_name("test_database")

    # Read videos with thumbnails (uses SQLite)
    videos = db.get_videos(include=["video_id", "with_thumbnails"])
    videos_with_thumbs = [v for v in videos if v.with_thumbnails]

    assert len(videos_with_thumbs) >= 0
    print(
        f"[OK] Successfully accessed SQLite thumbnails: {len(videos_with_thumbs)} videos with thumbnails"
    )


@pytest.mark.skip(reason="Experimental test for pyfakefs compatibility")
def test_pyfakefs_write_operation(fs):
    """Test write operations with pyfakefs."""
    fs.add_real_directory(TEST_HOME_DIR, read_only=False)

    app = Application(home_dir=TEST_HOME_DIR)
    db = app.open_database_from_name("test_database")

    # Add a property (writes to JSON and pickle)
    prop_name = "test_pyfakefs_prop"
    try:
        db.prop_type_add(prop_name, "str", "", True)
        props = db.get_prop_types(name=prop_name)
        assert len(props) == 1
        print("[OK] Successfully wrote property with pyfakefs")

        # Cleanup
        db.prop_type_del(prop_name)
    except Exception as e:
        pytest.fail(f"Write operation failed with pyfakefs: {e}")


@pytest.mark.skip(reason="Experimental test for pyfakefs compatibility")
def test_pyfakefs_set_tags(fs):
    """Test setting tags (writes to JSON, pickle, and SQLite for text search)."""
    fs.add_real_directory(TEST_HOME_DIR, read_only=False)

    app = Application(home_dir=TEST_HOME_DIR)
    db = app.open_database_from_name("test_database")

    # Add a property
    prop_name = "test_tag_pyfakefs"
    db.prop_type_add(prop_name, "str", "", True)

    # Get a video
    video = db.get_videos(include=["video_id"])[0]
    video_id = video.video_id

    # Set tags (this updates JSON, pickle, and potentially SQLite FTS)
    db.videos_tag_set(prop_name, {video_id: ["test_value"]})

    # Verify
    tags = db.videos_tag_get(prop_name, indices=[video_id])
    assert video_id in tags
    assert "test_value" in tags[video_id]
    print("[OK] Successfully set and retrieved tags with pyfakefs")

    # Cleanup
    db.prop_type_del(prop_name)


if __name__ == "__main__":
    # Run tests manually without pytest to see detailed errors
    from pyfakefs.fake_filesystem_unittest import Patcher

    print("Testing pyfakefs compatibility with JSON database...\n")

    # Test 1: Simple read
    print("Test 1: Simple read")
    try:
        with Patcher() as patcher:
            fs = patcher.fs
            test_pyfakefs_simple_read(fs)
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 70 + "\n")

    # Test 2: SQLite thumbnails
    print("Test 2: SQLite thumbnails")
    try:
        with Patcher() as patcher:
            fs = patcher.fs
            test_pyfakefs_sqlite_thumbnails(fs)
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 70 + "\n")

    # Test 3: Write operation
    print("Test 3: Write operation")
    try:
        with Patcher() as patcher:
            fs = patcher.fs
            test_pyfakefs_write_operation(fs)
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 70 + "\n")

    # Test 4: Set tags
    print("Test 4: Set tags")
    try:
        with Patcher() as patcher:
            fs = patcher.fs
            test_pyfakefs_set_tags(fs)
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 70)
    print("Tests completed. Check results above.")
