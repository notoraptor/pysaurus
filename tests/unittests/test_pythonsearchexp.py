"""Tests for pysaurus.core.pythonsearchexp — PythonSearchExp facade."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import pytest

from pysaurus.core.pythonsearchexp import PythonSearchExp
from pysaurus.core.searchexp import FieldType, SetType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ATTRS = {
    "width": FieldType.INT,
    "height": FieldType.INT,
    "found": FieldType.BOOL,
    "watched": FieldType.BOOL,
    "readable": FieldType.BOOL,
    "title": FieldType.STR,
    "filename": FieldType.STR,
    "extension": FieldType.STR,
    "size": FieldType.FILESIZE,
    "length": FieldType.DURATION,
    "date": FieldType.DATE,
    "frame_rate": FieldType.FLOAT,
    "audio_languages": FieldType.STR.as_set,
    "audio_bit_rate": FieldType.INT,
    "byte_rate": FieldType.FILESIZE,
}

_PROPS: dict[str, FieldType | SetType] = {
    "rating": FieldType.INT,
    "favorite": FieldType.BOOL,
    "category": FieldType.STR.as_set,
}

_VIDEO = SimpleNamespace(
    width=1920,
    height=1080,
    found=True,
    watched=False,
    readable=True,
    title="My Test Video",
    filename="/videos/my_test_video.mp4",
    extension=".mp4",
    size=1_500_000_000,
    length=5_400_000_000,
    date=datetime(2024, 3, 15).timestamp(),
    frame_rate=29.97,
    audio_languages={"eng", "fra"},
    audio_bit_rate=128_000,
    byte_rate=500_000,
)

_PROP_VALUES = {"rating": 8, "favorite": True, "category": {"action", "drama"}}

_SEARCH = PythonSearchExp(
    attributes=_ATTRS,
    properties=_PROPS,
    get_property=lambda obj, name: _PROP_VALUES[name],
)


def _eval(expr: str, video: SimpleNamespace = _VIDEO) -> bool:
    return _SEARCH.evaluate(expr, video)


# ===========================================================================
# Comparisons
# ===========================================================================


class TestComparisons:
    @pytest.mark.parametrize(
        "expr, expected",
        [
            ("width > 1080", True),
            ("width > 1920", False),
            ("width >= 1920", True),
            ("width < 1920", False),
            ("width <= 1920", True),
            ("width == 1920", True),
            ("width != 1920", False),
            ("height == 1080", True),
            ("height != 1080", False),
        ],
    )
    def test_int_comparison(self, expr: str, expected: bool):
        assert _eval(expr) is expected

    def test_float_comparison(self):
        assert _eval("frame_rate > 25.0") is True
        assert _eval("frame_rate < 25.0") is False

    def test_string_comparison(self):
        assert _eval('extension == ".mp4"') is True
        assert _eval('extension != ".avi"') is True

    def test_field_vs_field(self):
        assert _eval("width > height") is True
        assert _eval("height > width") is False

    def test_filesize_with_multiplier(self):
        assert _eval("size > 1gi") is True
        assert _eval("size < 1gi") is False

    def test_duration(self):
        assert _eval("length > 1h") is True
        assert _eval("length > 2h") is False


# ===========================================================================
# Boolean / is
# ===========================================================================


class TestBoolean:
    def test_bool_field_true(self):
        assert _eval("found") is True

    def test_bool_field_false(self):
        assert _eval("watched") is False

    def test_not_bool(self):
        assert _eval("not watched") is True
        assert _eval("not found") is False

    @pytest.mark.parametrize(
        "expr, expected",
        [
            ("found is True", True),
            ("found is False", False),
            ("watched is True", False),
            ("watched is False", True),
            ("found is not False", True),
        ],
    )
    def test_is_operator(self, expr: str, expected: bool):
        assert _eval(expr) is expected


# ===========================================================================
# in / not in
# ===========================================================================


class TestIn:
    def test_substring(self):
        assert _eval('"Test" in title') is True
        assert _eval('"absent" in title') is False

    def test_substring_not_in(self):
        assert _eval('"absent" not in title') is True
        assert _eval('"Test" not in title') is False

    def test_field_in_set_literal(self):
        assert _eval('extension in {".mp4", ".mkv"}') is True
        assert _eval('extension in {".avi", ".wmv"}') is False

    def test_field_not_in_set_literal(self):
        assert _eval('extension not in {".avi", ".wmv"}') is True

    def test_membership_in_set_field(self):
        assert _eval('"eng" in audio_languages') is True
        assert _eval('"jpn" in audio_languages') is False

    def test_membership_not_in_set_field(self):
        assert _eval('"jpn" not in audio_languages') is True

    def test_empty_set(self):
        assert _eval("extension in {}") is False


# ===========================================================================
# len()
# ===========================================================================


class TestLen:
    def test_len_string(self):
        assert _eval("len(title) > 5") is True
        assert _eval("len(title) == 13") is True

    def test_len_set(self):
        assert _eval("len(audio_languages) == 2") is True
        assert _eval("len(audio_languages) > 5") is False


# ===========================================================================
# Logical operators
# ===========================================================================


class TestLogical:
    def test_and_both_true(self):
        assert _eval("found and readable") is True

    def test_and_one_false(self):
        assert _eval("found and watched") is False

    def test_or_one_true(self):
        assert _eval("found or watched") is True

    def test_or_both_false(self):
        assert _eval("not found or watched") is False

    def test_xor(self):
        assert _eval("found xor watched") is True
        assert _eval("found xor readable") is False

    def test_short_circuit_and(self):
        """and short-circuits: if left is False, right is not evaluated."""
        assert _eval("watched and found") is False

    def test_short_circuit_or(self):
        """or short-circuits: if left is True, right is not evaluated."""
        assert _eval("found or watched") is True


# ===========================================================================
# Dates
# ===========================================================================


class TestDates:
    def test_date_literal_year(self):
        assert _eval("date > 2023") is True
        assert _eval("date > 2025") is False

    def test_date_literal_full(self):
        assert _eval("date == 2024-03-15") is True
        assert _eval("date > 2024-03-14") is True
        assert _eval("date < 2024-03-16") is True

    def test_date_timestamp(self):
        ts = _VIDEO.date
        assert _eval(f"date == {ts}") is True
        assert _eval(f"date > {ts - 1.0}") is True


# ===========================================================================
# Properties
# ===========================================================================


class TestProperties:
    def test_property_comparison(self):
        assert _eval("`rating` > 5") is True
        assert _eval("`rating` == 8") is True

    def test_property_bool(self):
        assert _eval("`favorite`") is True
        assert _eval("not `favorite`") is False

    def test_property_set_membership(self):
        assert _eval('"action" in `category`') is True
        assert _eval('"comedy" in `category`') is False


# ===========================================================================
# Complex expressions
# ===========================================================================


class TestComplex:
    def test_multi_condition(self):
        assert _eval('width > 1080 and "eng" in audio_languages and found') is True

    def test_multi_condition_fails(self):
        assert _eval("width > 1080 and watched and found") is False

    def test_parentheses(self):
        assert _eval("(found or watched) and readable") is True
        assert _eval("found or (watched and readable)") is True

    def test_mixed_attributes_and_properties(self):
        assert (
            _eval('width > 1080 and `rating` >= 8 and "action" in `category`') is True
        )


# ===========================================================================
# Error cases
# ===========================================================================


class TestErrors:
    def test_no_property_getter(self):
        search = PythonSearchExp(attributes=_ATTRS, properties=_PROPS)
        with pytest.raises(TypeError, match="No property getter"):
            search.evaluate("`rating` > 5", _VIDEO)
