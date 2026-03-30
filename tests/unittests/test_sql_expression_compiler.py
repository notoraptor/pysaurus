"""Tests for SqlExpressionCompiler — searchexp IR to SQL compilation."""

from __future__ import annotations

import pytest

from pysaurus.core.searchexp import ExpressionParser, FieldType
from pysaurus.database.saurus.sql_expression_compiler import (
    PropertyMeta,
    SqlExpressionCompiler,
    VIDEO_SEARCH_ATTRIBUTES,
    properties_to_field_types,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PROPS: dict[str, PropertyMeta] = {
    "rating": PropertyMeta(type="int", multiple=False),
    "favorite": PropertyMeta(type="bool", multiple=False),
    "category": PropertyMeta(type="str", multiple=True),
    "note": PropertyMeta(type="str", multiple=False),
}

_PROP_FIELD_TYPES = properties_to_field_types(_PROPS)

_PARSER = ExpressionParser(
    attributes=VIDEO_SEARCH_ATTRIBUTES, properties=_PROP_FIELD_TYPES
)
_COMPILER = SqlExpressionCompiler(properties=_PROPS)


def _compile(expr: str) -> tuple[str, list]:
    ir = _PARSER.parse(expr)
    return _COMPILER.compile(ir)


# ===========================================================================
# Comparisons on attributes
# ===========================================================================


class TestAttributeComparisons:
    def test_int_gt(self):
        sql, params = _compile("width > 1080")
        assert sql == "v.width > ?"
        assert params == [1080]

    def test_int_eq(self):
        sql, params = _compile("height == 1080")
        assert sql == "v.height = ?"
        assert params == [1080]

    def test_int_ne(self):
        sql, params = _compile("width != 1920")
        assert sql == "v.width != ?"
        assert params == [1920]

    def test_float_lt(self):
        sql, params = _compile("frame_rate < 30.0")
        assert sql == "v.frame_rate < ?"
        assert params == [30.0]

    def test_string_eq(self):
        sql, params = _compile('container_format == "mkv"')
        assert sql == "v.container_format = ?"
        assert params == ["mkv"]

    def test_field_vs_field(self):
        sql, params = _compile("width > height")
        assert sql == "v.width > v.height"
        assert params == []

    def test_filesize_with_multiplier(self):
        sql, params = _compile("size > 1gi")
        assert sql == "v.file_size > ?"
        assert params == [1073741824]

    def test_duration(self):
        sql, params = _compile("length > 1h")
        assert sql == "v.length_microseconds > ?"
        assert params == [3_600_000_000]

    def test_renamed_fields(self):
        sql, _ = _compile("size > 0")
        assert "v.file_size" in sql
        sql, _ = _compile("length > 0")
        assert "v.length_microseconds" in sql
        sql, _ = _compile("date > 2024")
        assert "v.mtime" in sql

    def test_extension(self):
        sql, params = _compile('extension == "mp4"')
        assert sql == "v.extension = ?"
        assert params == ["mp4"]

    def test_file_title(self):
        sql, params = _compile('"concert" in file_title')
        assert "INSTR(v.file_title, ?) > 0" == sql
        assert params == ["concert"]


# ===========================================================================
# Boolean / is
# ===========================================================================


class TestBoolean:
    def test_bare_bool(self):
        sql, params = _compile("found")
        assert sql == "v.found"
        assert params == []

    def test_is_true(self):
        sql, params = _compile("found is True")
        assert sql == "v.found = ?"
        assert params == [1]

    def test_is_false(self):
        sql, params = _compile("readable is False")
        assert sql == "v.readable = ?"
        assert params == [0]

    def test_not(self):
        sql, params = _compile("not watched")
        assert sql == "NOT (v.watched)"
        assert params == []


# ===========================================================================
# in / not in
# ===========================================================================


class TestIn:
    def test_substring_in_str(self):
        sql, params = _compile('"test" in filename')
        assert "INSTR(v.filename, ?) > 0" == sql
        assert params == ["test"]

    def test_substring_not_in_str(self):
        sql, params = _compile('"test" not in filename')
        assert "INSTR(v.filename, ?) = 0" == sql
        assert params == ["test"]

    def test_field_in_set_literal(self):
        sql, params = _compile('container_format in {"mkv", "mp4"}')
        assert "v.container_format IN" in sql
        assert set(params) == {"mkv", "mp4"}

    def test_field_not_in_set_literal(self):
        sql, params = _compile('container_format not in {"avi"}')
        assert "NOT v.container_format IN" in sql
        assert params == ["avi"]

    def test_empty_set(self):
        sql, params = _compile("container_format in {}")
        assert sql == "0"
        assert params == []

    def test_empty_set_negated(self):
        sql, params = _compile("container_format not in {}")
        assert sql == "1"
        assert params == []

    def test_in_set_field(self):
        sql, params = _compile('"eng" in audio_languages')
        assert "EXISTS" in sql
        assert "video_language" in sql
        assert "stream = 'a'" in sql
        assert "lang_code = ?" in sql
        assert params == ["eng"]

    def test_not_in_set_field(self):
        sql, params = _compile('"eng" not in audio_languages')
        assert "NOT EXISTS" in sql
        assert params == ["eng"]

    def test_in_subtitle_languages(self):
        sql, params = _compile('"fra" in subtitle_languages')
        assert "stream = 's'" in sql
        assert params == ["fra"]

    def test_in_errors(self):
        sql, params = _compile('"codec" in errors')
        assert "video_error" in sql
        assert "error = ?" in sql
        assert params == ["codec"]


# ===========================================================================
# len()
# ===========================================================================


class TestLen:
    def test_len_string(self):
        sql, params = _compile("len(filename) > 50")
        assert "LENGTH(v.filename)" in sql
        assert params == [50]

    def test_len_set_field(self):
        sql, params = _compile("len(audio_languages) > 2")
        assert "SELECT COUNT(*)" in sql
        assert "video_language" in sql
        assert "stream = 'a'" in sql
        assert params == [2]

    def test_len_errors(self):
        sql, params = _compile("len(errors) == 0")
        assert "SELECT COUNT(*)" in sql
        assert "video_error" in sql


# ===========================================================================
# Logical operators
# ===========================================================================


class TestLogical:
    def test_and(self):
        sql, params = _compile("found and readable")
        assert "AND" in sql
        assert "v.found" in sql
        assert "v.readable" in sql

    def test_or(self):
        sql, params = _compile("found or readable")
        assert "OR" in sql

    def test_xor(self):
        sql, params = _compile("found xor watched")
        assert "AND NOT" in sql
        assert "OR" in sql

    def test_complex_and_or(self):
        sql, params = _compile("width > 1080 and (found or readable)")
        assert "AND" in sql
        assert "OR" in sql
        assert params == [1080]


# ===========================================================================
# Dates
# ===========================================================================


class TestDates:
    def test_date_literal_year(self):
        sql, params = _compile("date > 2024")
        assert sql == "v.mtime > ?"
        assert len(params) == 1
        assert isinstance(params[0], float)

    def test_date_literal_full(self):
        sql, params = _compile("date > 2024-03-15")
        assert sql == "v.mtime > ?"
        assert len(params) == 1


# ===========================================================================
# Properties
# ===========================================================================


class TestProperties:
    def test_property_int_comparison(self):
        sql, params = _compile("`rating` > 5")
        assert "EXISTS" in sql
        assert "video_property_value" in sql
        assert "p.name = ?" in sql
        assert "CAST(vpv.property_value AS INTEGER)" in sql
        assert params == ["rating", 5]

    def test_property_bool_bare(self):
        sql, params = _compile("`favorite`")
        assert "EXISTS" in sql
        assert "p.name = ?" in sql
        assert "vpv.property_value = ?" in sql
        assert params == ["favorite", "1"]

    def test_property_bool_is_false(self):
        sql, params = _compile("`favorite` is False")
        assert params == ["favorite", "0"]

    def test_property_set_in(self):
        sql, params = _compile('"action" in `category`')
        assert "EXISTS" in sql
        assert "vpv.property_value = ?" in sql
        assert params == ["category", "action"]

    def test_property_set_not_in(self):
        sql, params = _compile('"action" not in `category`')
        assert "NOT EXISTS" in sql
        assert params == ["category", "action"]

    def test_property_str_contains(self):
        sql, params = _compile('"hello" in `note`')
        assert "INSTR(vpv.property_value, ?)" in sql
        assert params == ["note", "hello"]

    def test_property_str_not_contains(self):
        sql, params = _compile('"hello" not in `note`')
        assert "NOT EXISTS" in sql
        assert "INSTR" in sql

    def test_property_len(self):
        sql, params = _compile("len(`category`) > 2")
        assert "SELECT COUNT(*)" in sql
        assert "video_property_value" in sql
        assert params == ["category", 2]


# ===========================================================================
# Complex expressions
# ===========================================================================


class TestComplex:
    def test_multi_condition(self):
        sql, params = _compile('width > 1080 and "eng" in audio_languages and found')
        assert "v.width > ?" in sql
        assert "EXISTS" in sql
        assert "v.found" in sql
        assert 1080 in params
        assert "eng" in params

    def test_mixed_attributes_and_properties(self):
        sql, params = _compile("width > 1080 and `rating` >= 5")
        assert "v.width > ?" in sql
        assert "EXISTS" in sql
        assert "CAST(vpv.property_value AS INTEGER)" in sql


# ===========================================================================
# Error cases
# ===========================================================================


class TestErrors:
    def test_unknown_property(self):
        parser = ExpressionParser(
            attributes=VIDEO_SEARCH_ATTRIBUTES, properties={"unknown": FieldType.INT}
        )
        ir = parser.parse("`unknown` > 5")
        compiler = SqlExpressionCompiler(properties={})
        with pytest.raises(TypeError, match="Unknown property"):
            compiler.compile(ir)
