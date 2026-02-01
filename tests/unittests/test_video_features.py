import pytest

from pysaurus.video.video_features import VideoFeatures


class MockVideo:
    """Simple mock video object for testing."""

    def __init__(self, video_id: int, file_title: str):
        self.video_id = video_id
        self.file_title = file_title


class TestComputeDiffRanges:
    """Tests for VideoFeatures._compute_diff_ranges"""

    def test_identical_strings(self):
        """Identical strings should return empty list."""
        result = VideoFeatures._compute_diff_ranges("hello", "hello")
        assert result == []

    def test_completely_different_strings(self):
        """Completely different strings should return full range."""
        result = VideoFeatures._compute_diff_ranges("abc", "xyz")
        assert result == [(0, 3)]

    def test_single_character_difference_at_end(self):
        """Single character difference at the end."""
        result = VideoFeatures._compute_diff_ranges("video_01", "video_02")
        assert result == [(7, 8)]  # Only the last character differs

    def test_single_character_difference_at_start(self):
        """Single character difference at the start."""
        result = VideoFeatures._compute_diff_ranges("Avideo", "Bvideo")
        assert result == [(0, 1)]

    def test_single_character_difference_in_middle(self):
        """Single character difference in the middle."""
        result = VideoFeatures._compute_diff_ranges("video_a_test", "video_b_test")
        assert result == [(6, 7)]

    def test_multiple_differences(self):
        """Multiple differences in the string."""
        result = VideoFeatures._compute_diff_ranges("a1b2c", "x1y2z")
        # 'a' vs 'x' at 0, 'b' vs 'y' at 2, 'c' vs 'z' at 4
        assert result == [(0, 1), (2, 3), (4, 5)]

    def test_different_lengths_longer_text(self):
        """Reference shorter than text."""
        result = VideoFeatures._compute_diff_ranges("video", "video_extended")
        assert result == [(5, 14)]  # Extra part at the end

    def test_different_lengths_shorter_text(self):
        """Reference longer than text."""
        result = VideoFeatures._compute_diff_ranges("video_extended", "video")
        # The text is shorter, so no extra ranges after matching part
        assert result == []

    def test_empty_reference(self):
        """Empty reference string."""
        result = VideoFeatures._compute_diff_ranges("", "hello")
        assert result == [(0, 5)]

    def test_empty_text(self):
        """Empty text string."""
        result = VideoFeatures._compute_diff_ranges("hello", "")
        assert result == []

    def test_both_empty(self):
        """Both strings empty."""
        result = VideoFeatures._compute_diff_ranges("", "")
        assert result == []

    def test_realistic_filename_difference(self):
        """Realistic filename with number difference."""
        result = VideoFeatures._compute_diff_ranges(
            "My_Video_Episode_01_720p", "My_Video_Episode_02_720p"
        )
        # Only the "2" differs (index 18), the "0" is common
        assert result == [(18, 19)]

    def test_realistic_filename_multiple_numbers(self):
        """Realistic filename with multiple number differences."""
        result = VideoFeatures._compute_diff_ranges(
            "video_s01e01_720p", "video_s01e02_720p"
        )
        # Only the "2" differs (index 11), the "0" is common
        assert result == [(11, 12)]


class TestGetFileTitleDiffs:
    """Tests for VideoFeatures.get_file_title_diffs"""

    def test_empty_list(self):
        """Empty video list should return empty dict."""
        result = VideoFeatures.get_file_title_diffs([])
        assert result == {}

    def test_single_video(self):
        """Single video should return empty dict (need at least 2)."""
        videos = [MockVideo(1, "video_01")]
        result = VideoFeatures.get_file_title_diffs(videos)
        assert result == {}

    def test_two_identical_videos(self):
        """Two videos with identical titles."""
        videos = [
            MockVideo(1, "video_01"),
            MockVideo(2, "video_01"),
        ]
        result = VideoFeatures.get_file_title_diffs(videos)
        assert result == {1: [], 2: []}  # Reference has [], second has [] (no diff)

    def test_two_different_videos(self):
        """Two videos with different titles."""
        videos = [
            MockVideo(1, "video_01"),
            MockVideo(2, "video_02"),
        ]
        result = VideoFeatures.get_file_title_diffs(videos)
        assert result == {1: [], 2: [(7, 8)]}  # Reference has [], second has diff

    def test_three_videos(self):
        """Three videos with varying differences."""
        videos = [
            MockVideo(1, "video_01"),
            MockVideo(2, "video_02"),
            MockVideo(3, "video_03"),
        ]
        result = VideoFeatures.get_file_title_diffs(videos)
        assert result == {
            1: [],  # Reference
            2: [(7, 8)],  # "1" vs "2"
            3: [(7, 8)],  # "1" vs "3"
        }

    def test_first_video_is_reference(self):
        """First video in list is always the reference (empty diff list)."""
        videos = [
            MockVideo(100, "aaa"),
            MockVideo(200, "bbb"),
            MockVideo(300, "ccc"),
        ]
        result = VideoFeatures.get_file_title_diffs(videos)
        assert result[100] == []  # First video is always reference

    def test_none_file_title(self):
        """Handle None file_title gracefully."""
        videos = [
            MockVideo(1, None),
            MockVideo(2, "video"),
        ]
        result = VideoFeatures.get_file_title_diffs(videos)
        # None becomes "" via str(), so entire "video" is diff
        assert result == {1: [], 2: [(0, 5)]}

    def test_iterator_input(self):
        """Should work with iterators, not just lists."""
        def video_generator():
            yield MockVideo(1, "video_01")
            yield MockVideo(2, "video_02")

        result = VideoFeatures.get_file_title_diffs(video_generator())
        assert result == {1: [], 2: [(7, 8)]}

    def test_custom_getfield(self):
        """Test with custom getfield function (like dict access)."""
        videos = [
            {"id": 1, "title": "video_01"},
            {"id": 2, "title": "video_02"},
        ]
        result = VideoFeatures.get_file_title_diffs(
            videos,
            getfield=lambda obj, key: obj["id"] if key == "video_id" else obj["title"],
        )
        assert result == {1: [], 2: [(7, 8)]}
