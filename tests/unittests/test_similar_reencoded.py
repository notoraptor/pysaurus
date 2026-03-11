from types import SimpleNamespace

import pytest

from pysaurus.database.features.db_similar_reencoded import DbSimilarReencoded


def _video(title: str) -> SimpleNamespace:
    return SimpleNamespace(filename=SimpleNamespace(file_title=title))


def _titles_match(title1: str, title2: str) -> bool:
    return DbSimilarReencoded._titles_match(_video(title1), _video(title2))


class TestTitlesMatch:
    def test_identical_titles(self):
        assert _titles_match("video", "video")

    def test_short_title_with_suffix_within_min_threshold(self):
        # "NGOD-126" (8 chars) vs "NGOD-126 (hb)" (14 chars)
        # diff = 6, threshold = max(8*0.5, 8) = 8 => 6 < 8 => match
        assert _titles_match("NGOD-126", "NGOD-126 (hb)")

    def test_short_title_with_suffix_exceeding_min_threshold(self):
        # "NGOD-126" (8 chars) vs "NGOD-126 (extended cut)" (23 chars)
        # diff = 15, threshold = max(8*0.5, 8) = 8 => 15 < 8 => no match
        assert not _titles_match("NGOD-126", "NGOD-126 (extended cut)")

    def test_long_title_uses_ratio_not_min(self):
        # "a]very_long_title_here" (22 chars) vs "a very_long_title_here XY" (25 chars)
        # diff = 3, threshold = max(22*0.5, 8) = 11 => 3 < 11 => match
        assert _titles_match("a very_long_title_here", "a very_long_title_here XY")

    def test_long_title_ratio_rejects_large_suffix(self):
        # "long_title_here" (15 chars) vs "long_title_here appended_stuff" (30 chars)
        # diff = 15, threshold = max(15*0.5, 8) = 8 => 15 < 8 => no match
        assert not _titles_match("long_title_here", "long_title_here appended_stuff")

    def test_not_substring(self):
        assert not _titles_match("NGOD-126", "NGOD-127")

    def test_dash_vs_space_no_match(self):
        # Strict substring check: "NGOD-126" is not in "NGOD 126"
        assert not _titles_match("NGOD-126", "NGOD 126")

    def test_empty_title(self):
        assert not _titles_match("", "anything")

    def test_both_empty(self):
        assert not _titles_match("", "")

    def test_order_independent(self):
        assert _titles_match("NGOD-126 (hb)", "NGOD-126")
        assert _titles_match("NGOD-126", "NGOD-126 (hb)")

    @pytest.mark.parametrize(
        "short, long_name",
        [("video", "video (hb)"), ("clip", "clip (hb)"), ("abc", "abc (hb)")],
    )
    def test_hb_suffix_with_various_short_titles(self, short, long_name):
        # " (hb)" is 5 chars of suffix.
        # For titles shorter than 16 chars, MIN_TITLE_DIFF=8 applies.
        # 5 < 8 => always matches if shorter is substring.
        assert _titles_match(short, long_name)

    def test_suffix_exactly_at_min_threshold(self):
        # "NGOD-126" (8 chars) vs "NGOD-126 1234567" (16 chars)
        # diff = 8, threshold = max(8*0.5, 8) = 8 => 8 < 8 => no match (strict <)
        assert not _titles_match("NGOD-126", "NGOD-126 1234567")

    def test_suffix_one_below_min_threshold(self):
        # "NGOD-126" (8 chars) vs "NGOD-126 123456" (15 chars)
        # diff = 7, threshold = max(8*0.5, 8) = 8 => 7 < 8 => match
        assert _titles_match("NGOD-126", "NGOD-126 123456")
