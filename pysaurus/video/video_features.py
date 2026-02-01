from difflib import SequenceMatcher
from typing import Iterable


class VideoFeatures:
    @staticmethod
    def get_common_fields(videos: Iterable, *, fields: Iterable[str], getfield=getattr):
        if not hasattr(videos, "__len__"):
            videos = list(videos)
        if len(videos) < 2:
            return {}
        first_video, *other_videos = videos
        return {
            key: all(
                getfield(first_video, key) == getfield(other_video, key)
                for other_video in other_videos
            )
            for key in fields
        }

    @staticmethod
    def get_file_title_diffs(
        videos: Iterable, *, getfield=getattr
    ) -> dict[int, list[tuple[int, int]]]:
        """
        Compute character-level diff ranges for file titles in a similarity group.

        Uses the first video's file_title as reference. For each other video,
        computes which character ranges differ from the reference.

        Args:
            videos: Iterable of video objects with video_id and file_title attributes
            getfield: Function to get attributes (default: getattr)

        Returns:
            Dict mapping video_id to list of (start, end) tuples indicating
            character ranges that differ from the reference.
            The reference video has an empty list.
        """
        if not hasattr(videos, "__len__"):
            videos = list(videos)
        if len(videos) < 2:
            return {}

        first_video, *other_videos = videos
        reference_id = getfield(first_video, "video_id")
        reference_title = str(getfield(first_video, "file_title") or "").lower()

        result = {reference_id: []}  # Reference has no diffs

        for video in other_videos:
            video_id = getfield(video, "video_id")
            title = str(getfield(video, "file_title") or "").lower()
            result[video_id] = VideoFeatures._compute_diff_ranges(reference_title, title)

        return result

    @staticmethod
    def _compute_diff_ranges(reference: str, text: str) -> list[tuple[int, int]]:
        """
        Compute which character ranges in `text` differ from `reference`.

        Returns a list of (start, end) tuples indicating ranges in `text`
        that don't match the reference.
        """
        if reference == text:
            return []

        matcher = SequenceMatcher(None, reference, text)
        matching_blocks = matcher.get_matching_blocks()

        # Build list of differing ranges in text
        diff_ranges = []
        prev_end_in_text = 0

        for match in matching_blocks:
            # match.b = start in text
            # match.size = length of match
            if match.b > prev_end_in_text:
                diff_ranges.append((prev_end_in_text, match.b))
            prev_end_in_text = match.b + match.size

        return diff_ranges
