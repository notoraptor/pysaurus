"""Unit tests for VideoSorting, the single sort-spec parser/normalizer.

VideoSorting is now the one authority that turns a list of "+field"/"-field"
(or bare "field") strings into an ordered, deduplicated sort order. Everything
else (SQL ORDER BY, sidebar displays, the mock, parse_sorting) routes through it.
"""

from pysaurus.video.video_sorting import VideoSorting


class TestVideoSorting:
    def test_parses_signed_and_bare_fields(self):
        vs = VideoSorting(["-date", "+length", "width"])
        assert list(vs) == [("date", True), ("length", False), ("width", False)]

    def test_len(self):
        assert len(VideoSorting(["-date", "+length"])) == 2

    def test_deduplicates_keeping_first(self):
        vs = VideoSorting(["-date", "+length", "+date"])
        assert list(vs) == [("date", True), ("length", False)]

    def test_duplicate_keeps_first_direction(self):
        # A later duplicate wins nothing, even with the opposite direction.
        assert list(VideoSorting(["+date", "-date"])) == [("date", False)]

    def test_to_string_list_normalizes_signs(self):
        assert VideoSorting(["-width", "height"]).to_string_list() == [
            "-width",
            "+height",
        ]

    def test_to_string_list_after_dedup(self):
        assert VideoSorting(["-date", "+date", "width"]).to_string_list() == [
            "-date",
            "+width",
        ]

    def test_equality(self):
        assert VideoSorting(["-date"]) == VideoSorting(["-date"])
        assert VideoSorting(["-date"]) != VideoSorting(["+date"])

    def test_empty(self):
        vs = VideoSorting([])
        assert len(vs) == 0
        assert vs.to_string_list() == []
