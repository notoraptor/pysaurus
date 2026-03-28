"""Tests for pysaurus.core.searchexp — parser, type coercion, helpers."""

from __future__ import annotations

import calendar
from datetime import datetime

import pytest

from pysaurus.core.searchexp import (
    Comparison,
    ExpressionError,
    ExpressionParser,
    FieldRef,
    FieldType,
    FunctionCall,
    InOp,
    IsOp,
    LiteralValue,
    LogicalOp,
    NotOp,
    SetLiteral,
    SetType,
    fields_from_class,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_parser(**extra_attrs: FieldType) -> ExpressionParser:
    attrs = {
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
        **extra_attrs,
    }
    return ExpressionParser(attributes=attrs)


def _make_parser_with_props(
    props: dict[str, FieldType | SetType] | None = None,
) -> ExpressionParser:
    attrs = {
        "width": FieldType.INT,
        "found": FieldType.BOOL,
        "title": FieldType.STR,
        "audio_languages": FieldType.STR.as_set,
    }
    return ExpressionParser(attributes=attrs, properties=props or {})


def _safe_timestamp(dt: datetime) -> float:
    """Convert a naive datetime to local-time timestamp, even for old dates."""
    try:
        return dt.timestamp()
    except (OSError, OverflowError):
        utc_ts = calendar.timegm(dt.timetuple())
        local_offset = datetime(2000, 1, 1).timestamp() - calendar.timegm(
            datetime(2000, 1, 1).timetuple()
        )
        return utc_ts + local_offset


def _ts(date_str: str) -> float:
    """Convert a date string to local-time timestamp, matching parser behavior."""
    formats = [
        ("%Y-%m-%dT%H:%M:%S", 19),
        ("%Y-%m-%dT%H:%M", 16),
        ("%Y-%m-%dT%H", 13),
        ("%Y-%m-%d", 10),
        ("%Y-%m", 7),
    ]
    for fmt, expected_len in formats:
        if len(date_str) == expected_len:
            return _safe_timestamp(datetime.strptime(date_str, fmt))
    # Year only (any number of digits)
    return _safe_timestamp(datetime(int(date_str), 1, 1))


def _literal(node: Comparison, side: str = "right") -> LiteralValue:
    """Extract a LiteralValue from a Comparison node, with assertion."""
    child = getattr(node, side)
    assert isinstance(child, LiteralValue)
    return child


# ===========================================================================
# Literals — values and types verified through the public API
# ===========================================================================


class TestLiteralInt:
    def test_plain_int(self):
        p = _make_parser()
        node = p.parse("width > 42")
        lit = _literal(node)
        assert lit.value == 42
        assert lit.field_type == FieldType.INT

    def test_float_literal(self):
        p = _make_parser()
        node = p.parse("frame_rate > 3.14")
        lit = _literal(node)
        assert lit.value == 3.14
        assert lit.field_type == FieldType.FLOAT

    def test_float_multiplier(self):
        p = _make_parser()
        node = p.parse("size > 1.5gi")
        assert _literal(node).value == 1.5 * 1_073_741_824

    @pytest.mark.parametrize(
        "suffix, expected",
        [
            ("k", 128_000),
            ("m", 128_000_000),
            ("g", 128_000_000_000),
            ("t", 128_000_000_000_000),
            ("ki", 131_072),
            ("mi", 134_217_728),
            ("gi", 137_438_953_472),
            ("ti", 140_737_488_355_328),
            # Case insensitivity
            ("K", 128_000),
            ("MI", 134_217_728),
            ("GI", 137_438_953_472),
        ],
    )
    def test_multiplier(self, suffix: str, expected: int):
        p = _make_parser()
        node = p.parse(f"size > 128{suffix}")
        assert _literal(node).value == expected


class TestLiteralDuration:
    def test_simple(self):
        p = _make_parser()
        node = p.parse("length > 45s")
        lit = _literal(node)
        assert lit.value == 45_000_000
        assert lit.field_type == FieldType.DURATION

    def test_compound(self):
        p = _make_parser()
        node = p.parse("length > 1h30min")
        assert _literal(node).value == 3_600_000_000 + 30 * 60_000_000

    def test_all_components(self):
        p = _make_parser()
        node = p.parse("length > 2d5h10min30s100u")
        expected = (
            2 * 86_400_000_000
            + 5 * 3_600_000_000
            + 10 * 60_000_000
            + 30 * 1_000_000
            + 100
        )
        assert _literal(node).value == expected

    def test_case_insensitive(self):
        p = _make_parser()
        node = p.parse("length > 5MIN30S")
        assert _literal(node).value == 5 * 60_000_000 + 30 * 1_000_000

    @pytest.mark.parametrize(
        "expr",
        ["length > 5s10min", "length > 5min10h"],
        ids=["s_before_min", "min_before_h"],
    )
    def test_bad_order_raises(self, expr: str):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="decreasing order"):
            p.parse(expr)


class TestLiteralDate:
    @pytest.mark.parametrize(
        "date_str",
        [
            "2024",
            "2024-03",
            "2024-03-15",
            "2024-03-15T14",
            "2024-03-15T14:30",
            "2024-03-15T14:30:00",
        ],
        ids=["year", "month", "day", "hour", "minute", "second"],
    )
    def test_precision_levels(self, date_str: str):
        p = _make_parser()
        op = "==" if len(date_str) == 4 else ">"
        node = p.parse(f"date {op} {date_str}")
        lit = _literal(node)
        assert lit.value == _ts(date_str)
        assert lit.field_type == FieldType.DATE


class TestLiteralString:
    def test_double_quote(self):
        p = _make_parser()
        node = p.parse('"hello" in title')
        assert isinstance(node, InOp)
        assert isinstance(node.left, LiteralValue)
        assert node.left.value == "hello"
        assert node.left.field_type == FieldType.STR

    def test_single_quote(self):
        p = _make_parser()
        node = p.parse("'world' in title")
        assert isinstance(node, InOp)
        assert isinstance(node.left, LiteralValue)
        assert node.left.value == "world"

    def test_unterminated_raises(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Unterminated string"):
            p.parse('"hello in title')


class TestLiteralMisc:
    def test_empty_property_raises(self):
        p = _make_parser_with_props({"x": FieldType.INT})
        with pytest.raises(ExpressionError, match="Empty property"):
            p.parse("`` > 5")

    def test_unexpected_character_raises(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Unexpected character"):
            p.parse("width @ 5")

    def test_5min_is_duration(self):
        """5min must be parsed as a duration, not 5 * 1048576."""
        p = _make_parser()
        node = p.parse("length > 5min")
        lit = _literal(node)
        assert lit.value == 5 * 60_000_000
        assert lit.field_type == FieldType.DURATION

    def test_5mi_is_multiplier(self):
        """5mi must be parsed as 5 * 1048576, not a duration."""
        p = _make_parser()
        node = p.parse("size > 5mi")
        lit = _literal(node)
        assert lit.value == 5 * 1_048_576

    def test_5m_is_multiplier(self):
        """5m must be parsed as 5 * 1000000, not a duration."""
        p = _make_parser()
        node = p.parse("audio_bit_rate > 5m")
        assert _literal(node).value == 5_000_000

    def test_unterminated_property(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Unterminated property"):
            p.parse("`category")

    def test_invalid_numeric_literal(self):
        """Digits followed by an unrecognized suffix."""
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Invalid numeric"):
            p.parse("width > 5xyz")

    def test_duration_suffix_followed_by_identifier(self):
        """Duration-like token followed by alnum falls back to number parsing."""
        p = _make_parser()
        # "5swidth" — 5s looks like duration but followed by 'w', not a valid token
        with pytest.raises(ExpressionError):
            p.parse("5swidth > 1")

    def test_number_with_multiplier_min_ambiguity(self):
        """5min30s in a numeric context: tokenizer must distinguish min from mi."""
        p = _make_parser()
        node = p.parse("length > 5min30s")
        assert _literal(node).value == 5 * 60_000_000 + 30 * 1_000_000

    def test_duplicate_duration_suffix(self):
        """5s5s is two tokens (5s, 5s), not a single duration — parser rejects it."""
        p = _make_parser()
        with pytest.raises(ExpressionError):
            p.parse("length > 5s5s")

    def test_number_followed_by_identifier(self):
        """A number immediately followed by unknown alpha is invalid."""
        p = _make_parser()
        with pytest.raises(ExpressionError):
            p.parse("width > 5abc")

    def test_multiplier_m_before_identifier(self):
        """5m followed by identifier chars: 5 is a plain number, mfoo is ident."""
        p = _make_parser()
        with pytest.raises(ExpressionError):
            p.parse("width > 5mfoo")

    def test_multiplier_m_before_mi_suffix(self):
        """5mixy: 'mi' suffix skipped (followed by alnum), then 'm' sees 'mi'
        prefix but not 'min' → skip m too → invalid."""
        p = _make_parser()
        with pytest.raises(ExpressionError):
            p.parse("width > 5mixy")

    def test_multiplier_m_before_min_identifier(self):
        """5minfoo: duration path fails (trailing 'foo'), number path detects
        'm' + 'in' prefix → not a multiplier → returns None → invalid."""
        p = _make_parser()
        with pytest.raises(ExpressionError):
            p.parse("width > 5minfoo")


# ===========================================================================
# Parser — basic expressions
# ===========================================================================


class TestParserBasic:
    def test_simple_comparison(self):
        p = _make_parser()
        node = p.parse("width > 1080")
        assert isinstance(node, Comparison)
        assert node.op == ">"
        assert isinstance(node.left, FieldRef)
        assert node.left.name == "width"
        assert isinstance(node.right, LiteralValue)
        assert node.right.value == 1080

    def test_reversed_comparison(self):
        p = _make_parser()
        node = p.parse("1080 < width")
        assert isinstance(node, Comparison)
        assert node.op == "<"
        assert isinstance(node.left, LiteralValue)
        assert isinstance(node.right, FieldRef)

    def test_reversed_ambiguous_literal_coerced(self):
        """2024 < date: the literal is on the left, must be coerced to DATE."""
        p = _make_parser()
        node = p.parse("2024 < date")
        assert isinstance(node, Comparison)
        lit = _literal(node, side="left")
        assert lit.field_type == FieldType.DATE
        assert lit.value == _ts("2024")

    def test_field_vs_field(self):
        p = _make_parser()
        node = p.parse("width > height")
        assert isinstance(node, Comparison)
        assert isinstance(node.left, FieldRef)
        assert isinstance(node.right, FieldRef)

    def test_boolean_field_alone(self):
        p = _make_parser()
        node = p.parse("found")
        assert isinstance(node, FieldRef)
        assert node.field_type == FieldType.BOOL

    def test_not_boolean(self):
        p = _make_parser()
        node = p.parse("not found")
        assert isinstance(node, NotOp)
        assert isinstance(node.operand, FieldRef)

    @pytest.mark.parametrize(
        "expr, expected",
        [
            ("found is True", True),
            ("found is False", False),
            ("found is not True", False),
            ("found is not False", True),
        ],
    )
    def test_is_operator(self, expr: str, expected: bool):
        p = _make_parser()
        node = p.parse(expr)
        assert isinstance(node, IsOp)
        assert node.value is expected

    def test_string_in_field(self):
        p = _make_parser()
        node = p.parse('"test" in title')
        assert isinstance(node, InOp)
        assert not node.negated
        assert isinstance(node.left, LiteralValue)
        assert node.left.value == "test"

    def test_string_not_in_field(self):
        p = _make_parser()
        node = p.parse('"test" not in title')
        assert isinstance(node, InOp)
        assert node.negated

    def test_field_in_set(self):
        p = _make_parser()
        node = p.parse('extension in {".mp4", ".mkv"}')
        assert isinstance(node, InOp)
        assert isinstance(node.right, SetLiteral)
        assert len(node.right.elements) == 2
        assert node.right.elements[0].value == ".mp4"

    def test_membership_in_set_field(self):
        p = _make_parser()
        node = p.parse('"eng" in audio_languages')
        assert isinstance(node, InOp)
        assert isinstance(node.right, FieldRef)
        assert node.right.field_type == FieldType.STR.as_set

    def test_len_function(self):
        p = _make_parser()
        node = p.parse("len(filename) > 100")
        assert isinstance(node, Comparison)
        assert isinstance(node.left, FunctionCall)
        assert node.left.name == "len"
        assert node.left.result_type == FieldType.INT

    def test_len_on_set(self):
        p = _make_parser()
        node = p.parse("len(audio_languages) > 2")
        assert isinstance(node, Comparison)
        assert isinstance(node.left, FunctionCall)

    def test_parentheses(self):
        p = _make_parser()
        node = p.parse("(width > 1080)")
        assert isinstance(node, Comparison)

    def test_empty_set(self):
        p = _make_parser()
        node = p.parse("extension in {}")
        assert isinstance(node, InOp)
        assert isinstance(node.right, SetLiteral)
        assert len(node.right.elements) == 0

    def test_trailing_comma_in_set(self):
        p = _make_parser()
        node = p.parse('extension in {".mp4",}')
        assert isinstance(node, InOp)
        assert isinstance(node.right, SetLiteral)
        assert len(node.right.elements) == 1

    @pytest.mark.parametrize("op", ["==", "!=", "<", "<=", ">", ">="])
    def test_comparison_operator(self, op: str):
        p = _make_parser()
        node = p.parse(f"width {op} 100")
        assert isinstance(node, Comparison)
        assert node.op == op


# ===========================================================================
# Parser — logical operators
# ===========================================================================


class TestParserLogical:
    @pytest.mark.parametrize(
        "expr, expected_op",
        [
            ("width > 1080 and found", "and"),
            ("found or watched", "or"),
            ("found xor watched", "xor"),
        ],
    )
    def test_logical_op(self, expr: str, expected_op: str):
        p = _make_parser()
        node = p.parse(expr)
        assert isinstance(node, LogicalOp)
        assert node.op == expected_op

    def test_precedence_and_or(self):
        """and binds tighter than or."""
        p = _make_parser()
        node = p.parse("found or watched and readable")
        assert isinstance(node, LogicalOp)
        assert node.op == "or"
        assert isinstance(node.right, LogicalOp)
        assert node.right.op == "and"

    def test_precedence_xor(self):
        """xor binds between and and or."""
        p = _make_parser()
        node = p.parse("found or watched xor readable")
        assert isinstance(node, LogicalOp)
        assert node.op == "or"
        assert isinstance(node.right, LogicalOp)
        assert node.right.op == "xor"

    def test_parentheses_override(self):
        p = _make_parser()
        node = p.parse("(found or watched) and readable")
        assert isinstance(node, LogicalOp)
        assert node.op == "and"
        assert isinstance(node.left, LogicalOp)
        assert node.left.op == "or"

    def test_not_precedence(self):
        p = _make_parser()
        node = p.parse("not found and watched")
        assert isinstance(node, LogicalOp)
        assert node.op == "and"
        assert isinstance(node.left, NotOp)


# ===========================================================================
# Parser — type coercion
# ===========================================================================


class TestParserTypeCoercion:
    @pytest.mark.parametrize(
        "expr, expected_type, expected_value",
        [
            ("date > 2024", FieldType.DATE, _ts("2024")),
            ("size > 1000", FieldType.FILESIZE, 1000),
            ("length > 60000000", FieldType.DURATION, 60_000_000),
            ("date > 1700000000.0", FieldType.DATE, 1700000000.0),
        ],
        ids=["int_to_date", "int_to_filesize", "int_to_duration", "float_to_date"],
    )
    def test_literal_coercion(
        self, expr: str, expected_type: FieldType, expected_value: object
    ):
        p = _make_parser()
        lit = _literal(p.parse(expr))
        assert lit.field_type == expected_type
        assert lit.value == expected_value

    def test_bare_number_not_duration(self):
        """60 is an int, not 60 seconds — must write 60s for duration."""
        p = _make_parser()
        lit = _literal(p.parse("length > 60"))
        assert lit.field_type == FieldType.DURATION
        assert lit.value == 60

    def test_set_elements_coerced(self):
        p = _make_parser()
        node = p.parse("width in {720, 1080, 1440}")
        assert isinstance(node, InOp)
        assert isinstance(node.right, SetLiteral)
        for elem in node.right.elements:
            assert elem.field_type == FieldType.INT


# ===========================================================================
# Parser — error cases
# ===========================================================================


class TestParserErrors:
    def test_literal_vs_literal(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Both sides.*are literals"):
            p.parse("1080 < 2000")

    def test_unknown_attribute(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Unknown attribute"):
            p.parse("nonexistent > 5")

    def test_unknown_property(self):
        p = _make_parser_with_props({"rating": FieldType.INT})
        with pytest.raises(ExpressionError, match="Unknown property"):
            p.parse("`nonexistent` > 5")

    def test_is_on_non_boolean(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="boolean field"):
            p.parse("width is True")

    def test_ordering_on_bool(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="not supported"):
            p.parse("found > True")

    def test_incompatible_types(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Cannot compare"):
            p.parse('width > "hello"')

    @pytest.mark.parametrize(
        "expr",
        [
            "size > 1h",  # FileSize vs Duration
            "size > 2024-01-01",  # FileSize vs Date
            "length > 2024-01-01",  # Duration vs Date
        ],
        ids=["filesize_duration", "filesize_date", "duration_date"],
    )
    def test_cross_type_incompatible(self, expr: str):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Cannot compare"):
            p.parse(expr)

    def test_ordering_on_set(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="not supported"):
            p.parse('audio_languages > {"eng"}')

    def test_non_boolean_field_alone(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="used as boolean"):
            p.parse("width")

    def test_literal_alone(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="literal alone"):
            p.parse("42")

    def test_function_call_alone(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Function call alone"):
            p.parse("len(title)")

    def test_len_on_non_string_non_set(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="len.*requires"):
            p.parse("len(width) > 5")

    def test_logical_op_on_non_boolean(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="boolean operands") as exc_info:
            p.parse("width and found")
        assert exc_info.value.position == 6
        assert exc_info.value.length == 3

    def test_no_attributes_no_properties(self):
        with pytest.raises(ValueError, match="At least one"):
            ExpressionParser()

    def test_empty_expression(self):
        p = _make_parser()
        with pytest.raises(ExpressionError):
            p.parse("")

    def test_in_requires_str_or_set_right(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="str or set"):
            p.parse("width in height")

    def test_property_without_properties_defined(self):
        p = ExpressionParser(attributes={"width": FieldType.INT})
        with pytest.raises(ExpressionError, match="Unknown property"):
            p.parse("`rating` > 5")

    def test_attribute_without_attributes_defined(self):
        p = ExpressionParser(properties={"rating": FieldType.INT})
        with pytest.raises(ExpressionError, match="Unknown attribute"):
            p.parse("width > 5")

    def test_unknown_attribute_no_attributes_defined(self):
        """Properties-only parser: unknown identifier says 'no attributes defined'."""
        p = ExpressionParser(properties={"rating": FieldType.INT})
        with pytest.raises(ExpressionError, match="no attributes defined"):
            p.parse("whatever > 5")

    def test_unknown_property_no_properties_defined(self):
        """Attributes-only parser: unknown property says 'no properties defined'."""
        p = ExpressionParser(attributes={"width": FieldType.INT})
        with pytest.raises(ExpressionError, match="no properties defined"):
            p.parse("`unknown` > 5")

    def test_is_followed_by_non_boolean(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Expected True or False"):
            p.parse("found is 42")

    def test_syntax_error_missing_rparen(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Expected RPAREN"):
            p.parse("(width > 1080")

    def test_incompatible_in_set_membership(self):
        """Type mismatch between left operand and set element type."""
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Cannot coerce"):
            p.parse('width in {"hello", "world"}')

    def test_set_mixed_incompatible_types(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Mixed types"):
            p.parse('extension in {42, "hello"}')

    def test_set_int_float_promotion(self):
        """Mixing int and float in a set promotes to float."""
        p = _make_parser()
        node = p.parse("frame_rate in {24, 29.97, 60}")
        assert isinstance(node, InOp)
        assert isinstance(node.right, SetLiteral)
        assert node.right.element_type == FieldType.FLOAT

    def test_set_equality_coerces_elements(self):
        """audio_languages == {"eng"}: set comparison, elements already match."""
        p = _make_parser()
        node = p.parse('audio_languages == {"eng", "fra"}')
        assert isinstance(node, Comparison)
        assert isinstance(node.right, SetLiteral)
        assert node.right.element_type == FieldType.STR

    def test_set_equality_coerces_int_to_date(self):
        """Set of dates field == {2024}: int elements coerced to date timestamps."""
        p = ExpressionParser(attributes={"dates": FieldType.DATE.as_set})
        node = p.parse("dates == {2024}")
        assert isinstance(node, Comparison)
        assert isinstance(node.right, SetLiteral)
        assert node.right.element_type == FieldType.DATE
        assert node.right.elements[0].value == _ts("2024")

    def test_set_equality_incompatible_elements(self):
        """audio_languages == {42}: int can't coerce to str → error."""
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Cannot coerce"):
            p.parse("audio_languages == {42}")

    def test_set_with_date_elements(self):
        p = _make_parser()
        node = p.parse("date in {2024-01-01, 2024-06-15}")
        assert isinstance(node, InOp)
        assert isinstance(node.right, SetLiteral)
        assert node.right.element_type == FieldType.DATE

    def test_set_with_duration_elements(self):
        p = _make_parser()
        node = p.parse("length in {30s, 1min, 5min}")
        assert isinstance(node, InOp)
        assert isinstance(node.right, SetLiteral)
        assert node.right.element_type == FieldType.DURATION

    def test_set_with_boolean_elements(self):
        p = _make_parser()
        node = p.parse("found in {True, False}")
        assert isinstance(node, InOp)
        assert isinstance(node.right, SetLiteral)
        assert len(node.right.elements) == 2

    def test_set_invalid_element(self):
        """Identifiers are not allowed inside set literals."""
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Expected a literal in set"):
            p.parse("width in {height, 1080}")

    def test_logical_op_with_literal(self):
        p = _make_parser()
        with pytest.raises(
            ExpressionError, match="boolean operands.*literal"
        ) as exc_info:
            p.parse("True and 42")
        assert exc_info.value.position == 5
        assert exc_info.value.length == 3

    def test_logical_op_with_function_call(self):
        p = _make_parser()
        with pytest.raises(
            ExpressionError, match="boolean operands.*function"
        ) as exc_info:
            p.parse("found and len(title)")
        assert exc_info.value.position == 6
        assert exc_info.value.length == 3

    def test_logical_op_with_set_literal(self):
        p = _make_parser()
        with pytest.raises(ExpressionError, match="boolean operands.*set") as exc_info:
            p.parse('found and {"a", "b"}')
        assert exc_info.value.position == 6
        assert exc_info.value.length == 3

    @pytest.mark.parametrize(
        "expr, expected_type, expected_value",
        [
            ("length > 1.5", FieldType.DURATION, 1.5),
            ("size > 1.5", FieldType.FILESIZE, 1.5),
            ("date > 1700000000.5", FieldType.DATE, 1700000000.5),
        ],
        ids=["float_to_duration", "float_to_filesize", "float_to_date"],
    )
    def test_float_coercion(
        self, expr: str, expected_type: FieldType, expected_value: float
    ):
        p = _make_parser()
        lit = _literal(p.parse(expr))
        assert lit.field_type == expected_type
        assert lit.value == expected_value

    def test_is_literal_on_left(self):
        """'is' requires a field, not a literal."""
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Expected a field"):
            p.parse("True is True")

    def test_in_membership_incompatible_types(self):
        """Literal type incompatible with set field element type."""
        p = _make_parser_with_props({"tags": FieldType.STR.as_set})
        with pytest.raises(ExpressionError, match="Cannot test"):
            p.parse("42 in `tags`")

    def test_in_literal_in_non_str_non_set_field(self):
        """'in' with non-str, non-set right side (e.g. int field)."""
        p = _make_parser()
        with pytest.raises(ExpressionError, match="str or set"):
            p.parse("42 in width")

    def test_not_in_as_standalone(self):
        """'not in' handled at comparison level, not as 'not' + 'in'."""
        p = _make_parser()
        node = p.parse('"test" not in title')
        assert isinstance(node, InOp)
        assert node.negated

    def test_not_wrapping_not_in(self):
        """not (x not in y): outer 'not' enters _parse_not, inner triggers backtrack."""
        p = _make_parser()
        node = p.parse('not "x" not in title')
        assert isinstance(node, NotOp)
        assert isinstance(node.operand, InOp)
        assert node.operand.negated

    def test_bare_not_in_backtracks(self):
        """'not in' without left operand: _parse_not backtracks then fails."""
        p = _make_parser()
        with pytest.raises(ExpressionError):
            p.parse("found and not in title")

    def test_field_in_field_set(self):
        """Field in set-typed field (both sides are fields)."""
        p = _make_parser()
        node = p.parse("extension in audio_languages")
        assert isinstance(node, InOp)

    def test_float_to_int_exact_with_multiplier(self):
        """2.0k = 2000.0 — parse_number already converts to int 2000."""
        p = _make_parser()
        node = p.parse("width > 2.0k")
        lit = _literal(node)
        assert lit.value == 2000
        assert isinstance(lit.value, int)

    def test_float_to_int_exact_plain(self):
        """2.0 (plain float) coerced to int for an int field."""
        p = _make_parser()
        node = p.parse("width > 2.0")
        lit = _literal(node)
        assert lit.value == 2
        assert isinstance(lit.value, int)
        assert lit.field_type == FieldType.INT

    def test_any_int_coerced_to_year(self):
        """100 compared to a date field: always interpreted as year 100."""
        p = _make_parser()
        node = p.parse("date > 100")
        lit = _literal(node)
        assert lit.field_type == FieldType.DATE
        assert lit.value == _ts("0100")

    def test_scalar_vs_set_field_incompatible(self):
        """Comparing a scalar field to a set field: type mismatch."""
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Cannot compare"):
            p.parse("width == audio_languages")

    def test_scalar_field_eq_set_literal(self):
        """width == {1, 2}: scalar field compared to set literal → error."""
        p = _make_parser()
        with pytest.raises(ExpressionError, match="Cannot compare"):
            p.parse("width == {1, 2}")

    def test_set_literal_on_left_eq(self):
        """{"eng", "fra"} == audio_languages: set literal on left side, coerced."""
        p = _make_parser()
        node = p.parse('{"eng", "fra"} == audio_languages')
        assert isinstance(node, Comparison)
        assert isinstance(node.left, SetLiteral)
        assert node.left.element_type == FieldType.STR

    def test_comparison_with_boolean_subexpression(self):
        """(width > 1080) == True: inner comparison used as operand."""
        p = _make_parser()
        node = p.parse("(width > 1080) == True")
        assert isinstance(node, Comparison)
        assert isinstance(node.left, Comparison)
        assert isinstance(node.right, LiteralValue)
        assert node.right.value is True

    def test_node_type_of_boolean_expression(self):
        """Nested boolean expressions should be valid in logical ops."""
        p = _make_parser()
        node = p.parse("(width > 100) and (height > 100)")
        assert isinstance(node, LogicalOp)


# ===========================================================================
# Parser — properties
# ===========================================================================


class TestParserProperties:
    def test_property_comparison(self):
        p = _make_parser_with_props({"rating": FieldType.INT})
        node = p.parse("`rating` > 5")
        assert isinstance(node, Comparison)
        assert isinstance(node.left, FieldRef)
        assert node.left.source == "property"
        assert node.left.name == "rating"
        assert node.left.field_type == FieldType.INT

    def test_property_bool(self):
        p = _make_parser_with_props({"favorite": FieldType.BOOL})
        node = p.parse("`favorite`")
        assert isinstance(node, FieldRef)
        assert node.field_type == FieldType.BOOL

    def test_property_in_set(self):
        p = _make_parser_with_props({"category": FieldType.STR.as_set})
        node = p.parse('"action" in `category`')
        assert isinstance(node, InOp)
        assert isinstance(node.right, FieldRef)
        assert node.right.source == "property"

    def test_mixed_attributes_and_properties(self):
        p = _make_parser_with_props({"rating": FieldType.INT})
        node = p.parse("width > 1080 and `rating` >= 8")
        assert isinstance(node, LogicalOp)


# ===========================================================================
# Parser — keyword case insensitivity
# ===========================================================================


class TestParserCaseInsensitivity:
    @pytest.mark.parametrize(
        "expr, expected_op",
        [
            ("found AND watched", "and"),
            ("found Or watched", "or"),
            ("found XOR watched", "xor"),
        ],
    )
    def test_logical_keyword(self, expr: str, expected_op: str):
        p = _make_parser()
        node = p.parse(expr)
        assert isinstance(node, LogicalOp)
        assert node.op == expected_op

    def test_not_uppercase(self):
        p = _make_parser()
        node = p.parse("NOT found")
        assert isinstance(node, NotOp)

    def test_is_true_uppercase(self):
        p = _make_parser()
        node = p.parse("found IS TRUE")
        assert isinstance(node, IsOp)
        assert node.value is True

    def test_is_not_uppercase(self):
        p = _make_parser()
        node = p.parse("found IS NOT True")
        assert isinstance(node, IsOp)
        assert node.value is False

    def test_in_uppercase(self):
        p = _make_parser()
        node = p.parse('"eng" IN audio_languages')
        assert isinstance(node, InOp)
        assert not node.negated

    def test_len_uppercase(self):
        p = _make_parser()
        node = p.parse("LEN(title) > 10")
        assert isinstance(node, Comparison)
        assert isinstance(node.left, FunctionCall)


# ===========================================================================
# fields_from_class tests
# ===========================================================================


class TestFieldsFromClass:
    def test_basic_annotations(self):
        class MyObj:
            name: str
            age: int
            score: float
            active: bool

        result = fields_from_class(MyObj)
        assert result == {
            "name": FieldType.STR,
            "age": FieldType.INT,
            "score": FieldType.FLOAT,
            "active": FieldType.BOOL,
        }

    def test_exclude(self):
        class MyObj:
            name: str
            age: int
            secret: str

        result = fields_from_class(MyObj, exclude={"secret"})
        assert "secret" not in result
        assert "name" in result

    def test_custom_type_mapping(self):
        class Duration:
            pass

        class MyObj:
            name: str
            length: Duration

        result = fields_from_class(MyObj, type_mapping={Duration: FieldType.DURATION})
        assert result["length"] == FieldType.DURATION

    def test_list_becomes_set(self):
        class MyObj:
            tags: list[str]

        result = fields_from_class(MyObj)
        assert result["tags"] == FieldType.STR.as_set

    def test_bare_list_raises(self):
        """list without type arg cannot determine element type → TypeError."""

        class MyObj:
            items: list

        with pytest.raises(TypeError, match="Cannot resolve"):
            fields_from_class(MyObj)

    def test_list_of_unknown_type_raises(self):
        """list[UnknownType] → element type not resolvable → TypeError."""

        class Custom:
            pass

        # Build the class without from __future__ import annotations
        # so get_type_hints resolves the annotation to list[Custom].
        MyObj = type("MyObj", (), {"__annotations__": {"items": list[Custom]}})

        with pytest.raises(TypeError, match="Cannot resolve"):
            fields_from_class(MyObj)

    def test_unknown_type_raises(self):
        class Unknown:
            pass

        class MyObj:
            weird: Unknown

        with pytest.raises(TypeError, match="Cannot resolve"):
            fields_from_class(MyObj)

    def test_private_fields_excluded(self):
        class MyObj:
            name: str
            _internal: int

        result = fields_from_class(MyObj)
        assert "_internal" not in result

    def test_optional_type(self):
        class MyObj:
            name: str | None

        result = fields_from_class(MyObj)
        assert result["name"] == FieldType.STR


# ===========================================================================
# Complex / integration tests
# ===========================================================================


class TestParserComplex:
    def test_complex_expression(self):
        p = _make_parser_with_props({"category": FieldType.STR.as_set})
        node = p.parse(
            'width > 1080 and "eng" in audio_languages and "action" in `category`'
        )
        assert isinstance(node, LogicalOp)

    def test_nested_not(self):
        p = _make_parser()
        node = p.parse("not not found")
        assert isinstance(node, NotOp)
        assert isinstance(node.operand, NotOp)
        assert isinstance(node.operand.operand, FieldRef)

    def test_not_in_with_set(self):
        p = _make_parser()
        node = p.parse('extension not in {".avi", ".wmv"}')
        assert isinstance(node, InOp)
        assert node.negated

    def test_multiple_conditions(self):
        p = _make_parser()
        node = p.parse("width > 1080 and height > 720 and found and not watched")
        assert isinstance(node, LogicalOp)
        assert node.op == "and"

    def test_filesize_comparison_with_multiplier(self):
        p = _make_parser()
        node = p.parse("size > 1.5gi")
        assert isinstance(node, Comparison)
        assert isinstance(node.right, LiteralValue)
        assert node.right.value == 1.5 * 1073741824

    def test_duration_comparison(self):
        p = _make_parser()
        node = p.parse("length > 1h30min")
        assert isinstance(node, Comparison)
        assert isinstance(node.right, LiteralValue)
        expected_us = 3600_000_000 + 30 * 60_000_000
        assert node.right.value == expected_us

    def test_len_equals_zero(self):
        p = _make_parser()
        node = p.parse("len(audio_languages) == 0")
        assert isinstance(node, Comparison)
        assert node.op == "=="
        assert isinstance(node.left, FunctionCall)
        assert isinstance(node.right, LiteralValue)
        assert node.right.value == 0
