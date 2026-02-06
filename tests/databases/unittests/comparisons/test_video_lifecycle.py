"""
Tests for complete video lifecycle: scan/add → delete.

These tests use a real minimal test video (test_video_minimal.mp4)
stored in tests/fixtures/ and committed to git.

The approach:
1. Create a temporary directory
2. Copy the test video to the temp directory
3. Add the temp directory to database folders
4. Scan/update to add the video
5. Test operations (delete, etc.)
6. Verify both database and filesystem state
"""

import shutil
from pathlib import Path


# Path to the minimal test video (committed to git)
TEST_VIDEO_PATH = (
    Path(__file__).parent.parent.parent.parent / "fixtures" / "test_video_minimal.mp4"
)


class TestVideoLifecycleAdd:
    """Test adding videos via folder scan."""

    def test_video_add_via_scan(self, mem_old_database, mem_saurus_database, tmp_path):
        """Test that scanning a folder adds a new video to both databases."""
        # Verify test video exists
        assert TEST_VIDEO_PATH.exists(), f"Test video not found: {TEST_VIDEO_PATH}"

        # Create temp directory and copy test video
        temp_video_dir = tmp_path / "test_videos"
        temp_video_dir.mkdir()
        temp_video_path = temp_video_dir / "scan_test_video.mp4"
        shutil.copy(TEST_VIDEO_PATH, temp_video_path)

        assert temp_video_path.exists(), "Failed to copy test video"

        # Verify video is NOT in databases yet
        old_videos_before = mem_old_database.get_videos(include=["filename"])
        new_videos_before = mem_saurus_database.get_videos(include=["filename"])

        old_filenames_before = {str(v.filename) for v in old_videos_before}
        new_filenames_before = {str(v.filename) for v in new_videos_before}

        assert str(temp_video_path) not in old_filenames_before, (
            "Video already in JSON database"
        )
        assert str(temp_video_path) not in new_filenames_before, (
            "Video already in SQL database"
        )

        # Add temp directory to database folders
        from pysaurus.core.absolute_path import AbsolutePath

        old_folders = list(mem_old_database.get_folders())
        new_folders = list(mem_saurus_database.get_folders())

        old_folders.append(AbsolutePath.ensure(temp_video_dir))
        new_folders.append(AbsolutePath.ensure(temp_video_dir))

        mem_old_database._set_folders(old_folders)
        mem_saurus_database._set_folders(new_folders)

        # Scan/update databases to add the video
        from pysaurus.database.database_algorithms import DatabaseAlgorithms

        old_algo = DatabaseAlgorithms(mem_old_database)
        new_algo = DatabaseAlgorithms(mem_saurus_database)

        # Update (scan for new videos)
        old_algo.update()
        new_algo.update()

        # Verify video is NOW in databases
        old_videos_after = mem_old_database.get_videos(include=["filename", "video_id"])
        new_videos_after = mem_saurus_database.get_videos(
            include=["filename", "video_id"]
        )

        old_filenames_after = {str(v.filename): v.video_id for v in old_videos_after}
        new_filenames_after = {str(v.filename): v.video_id for v in new_videos_after}

        assert str(temp_video_path) in old_filenames_after, (
            "Video not added to JSON database"
        )
        assert str(temp_video_path) in new_filenames_after, (
            "Video not added to SQL database"
        )

        # Get video_ids
        old_video_id = old_filenames_after[str(temp_video_path)]
        new_video_id = new_filenames_after[str(temp_video_path)]

        print("Video added successfully:")
        print(f"  JSON video_id: {old_video_id}")
        print(f"  SQL video_id: {new_video_id}")

        # Verify counts increased
        assert len(old_videos_after) == len(old_videos_before) + 1, (
            "JSON count didn't increase"
        )
        assert len(new_videos_after) == len(new_videos_before) + 1, (
            "SQL count didn't increase"
        )


class TestVideoLifecycleDelete:
    """Test deleting videos with DatabaseOperations."""

    def test_video_delete_complete(self, mem_old_database, tmp_path):
        """
        Test complete video deletion: scan → delete from DB → verify file deleted.

        Note: Only tests with mem_old_database because:
        - mem_old_database copies files to tmp_path
        - mem_saurus_database only copies DB to memory, not files
        - So we can safely test physical file deletion with mem_old_database
        """
        from pysaurus.database.database_algorithms import DatabaseAlgorithms
        from pysaurus.database.database_operations import DatabaseOperations

        # Verify test video exists
        assert TEST_VIDEO_PATH.exists(), f"Test video not found: {TEST_VIDEO_PATH}"

        # Create temp directory and copy test video
        temp_video_dir = tmp_path / "test_videos_delete"
        temp_video_dir.mkdir()
        temp_video_path = temp_video_dir / "delete_test_video.mp4"
        shutil.copy(TEST_VIDEO_PATH, temp_video_path)

        assert temp_video_path.exists(), "Failed to copy test video"

        # Add temp directory to database folders
        from pysaurus.core.absolute_path import AbsolutePath

        folders = list(mem_old_database.get_folders())
        folders.append(AbsolutePath.ensure(temp_video_dir))
        mem_old_database._set_folders(folders)

        # Scan to add the video
        algo = DatabaseAlgorithms(mem_old_database)
        algo.update()

        # Find the video in database by filename
        videos = mem_old_database.get_videos(include=["filename", "video_id"])
        video_dict = {str(v.filename): v.video_id for v in videos}

        assert str(temp_video_path) in video_dict, (
            "Video not added to database after scan"
        )
        video_id = video_dict[str(temp_video_path)]

        print(f"Video added with video_id: {video_id}")

        # Verify file exists before deletion
        assert temp_video_path.exists(), "Video file should exist before deletion"

        # Count videos before deletion
        count_before = len(mem_old_database.get_videos())

        # Delete the video using DatabaseOperations (deletes both file and DB entry)
        ops = DatabaseOperations(mem_old_database)

        # Initialize provider (needed for JSON database)
        if hasattr(mem_old_database, "provider"):
            mem_old_database.provider.get_view_indices()

        returned_path = ops.delete_video(video_id)

        # Verify returned path matches
        assert str(returned_path) == str(temp_video_path), "Returned path should match"

        # Verify file was DELETED from filesystem
        assert not temp_video_path.exists(), (
            "Video file should be deleted from filesystem"
        )

        # Verify video was DELETED from database
        count_after = len(mem_old_database.get_videos())
        assert count_after == count_before - 1, "Video count should decrease by 1"

        videos_after = mem_old_database.get_videos(include=["video_id"])
        video_ids_after = {v.video_id for v in videos_after}

        assert video_id not in video_ids_after, "Video should not exist in database"

        print("Video deleted successfully:")
        print(f"  video_id: {video_id}")
        print(f"  File deleted: {temp_video_path}")
        print("  DB entry deleted: Yes")
