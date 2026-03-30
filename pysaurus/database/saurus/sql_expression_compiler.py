"""Compile searchexp IR to SQL WHERE clauses for Pysaurus video queries.

The compiler walks the IR tree produced by ExpressionParser and generates
a (sql_where, params) tuple that can be injected into a QueryMaker via
where_builder.append_query(sql_where, *params).

All SQL expressions assume the video table is aliased as ``v`` and the
thumbnail table as ``vt`` (both set up by video_mega_group's QueryMaker).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pysaurus.core.searchexp.types import (
    Comparison,
    ComparisonOp,
    DateLiteral,
    DateTimestamp,
    FieldRef,
    FieldType,
    FunctionCall,
    InOp,
    IsOp,
    LiteralValue,
    LogicalOp,
    Node,
    NotOp,
    SetLiteral,
    SetType,
)
from pysaurus.core.universal_datetime import UDT

# Type alias for (sql_string, parameters)
SqlFragment = tuple[str, list[Any]]


@dataclass(frozen=True, slots=True)
class SetFieldMapping:
    """SQL mapping for a set field stored in a separate table."""

    table: str  # e.g., "video_language"
    column: str  # value column, e.g., "lang_code"
    extra_filter: str | None  # additional WHERE clause, e.g., "stream = 'a'"


@dataclass(frozen=True, slots=True)
class PropertyMeta:
    """Metadata about a custom property, for SQL compilation."""

    type: str  # "bool", "int", "float", "str"
    multiple: bool


# ── Pysaurus video field mappings ──────────────────────────────────────

# Scalar attributes: searchexp name → SQL column expression
ATTRIBUTE_SQL_MAP: dict[str, str] = {
    # Direct columns
    "audio_bit_rate": "v.audio_bit_rate",
    "audio_bits": "v.audio_bits",
    "audio_codec": "v.audio_codec",
    "audio_codec_description": "v.audio_codec_description",
    "bit_depth": "v.bit_depth",
    "channels": "v.channels",
    "container_format": "v.container_format",
    "device_name": "v.device_name",
    "extension": "v.extension",
    "file_title": "v.file_title",
    "filename": "v.filename",
    "height": "v.height",
    "meta_title": "v.meta_title",
    "sample_rate": "v.sample_rate",
    "video_codec": "v.video_codec",
    "video_codec_description": "v.video_codec_description",
    "video_id": "v.video_id",
    "watched": "v.watched",
    "width": "v.width",
    # Generated columns
    "found": "v.found",
    "readable": "v.readable",
    "frame_rate": "v.frame_rate",
    "byte_rate": "v.byte_rate",
    # Renamed
    "size": "v.file_size",
    "length": "v.length_microseconds",
    "date": "v.mtime",
    "date_entry_modified": "v.date_entry_modified_not_null",
    "date_entry_opened": "v.date_entry_opened_not_null",
    # Requires LEFT JOIN video_thumbnail (already present in video_mega_group)
    "with_thumbnails": "IIF(LENGTH(vt.thumbnail), 1, 0)",
}

# Set attributes: stored in separate tables
SET_FIELD_MAP: dict[str, SetFieldMapping] = {
    "audio_languages": SetFieldMapping("video_language", "lang_code", "stream = 'a'"),
    "subtitle_languages": SetFieldMapping(
        "video_language", "lang_code", "stream = 's'"
    ),
    "errors": SetFieldMapping("video_error", "error", None),
}

# ExpressionParser attribute configuration for Pysaurus video search
VIDEO_SEARCH_ATTRIBUTES: dict[str, FieldType | SetType] = {
    "audio_bit_rate": FieldType.INT,
    "audio_bits": FieldType.INT,
    "audio_codec": FieldType.STR,
    "audio_codec_description": FieldType.STR,
    "audio_languages": FieldType.STR.as_set,
    "bit_depth": FieldType.INT,
    "byte_rate": FieldType.FILESIZE,
    "channels": FieldType.INT,
    "container_format": FieldType.STR,
    "date": FieldType.DATE,
    "date_entry_modified": FieldType.DATE,
    "date_entry_opened": FieldType.DATE,
    "device_name": FieldType.STR,
    "errors": FieldType.STR.as_set,
    "extension": FieldType.STR,
    "file_title": FieldType.STR,
    "filename": FieldType.STR,
    "found": FieldType.BOOL,
    "frame_rate": FieldType.FLOAT,
    "height": FieldType.INT,
    "length": FieldType.DURATION,
    "meta_title": FieldType.STR,
    "readable": FieldType.BOOL,
    "sample_rate": FieldType.INT,
    "size": FieldType.FILESIZE,
    "subtitle_languages": FieldType.STR.as_set,
    "video_codec": FieldType.STR,
    "video_codec_description": FieldType.STR,
    "video_id": FieldType.INT,
    "watched": FieldType.BOOL,
    "width": FieldType.INT,
    "with_thumbnails": FieldType.BOOL,
}

# SQL CAST expressions per property type
_PROPERTY_CAST: dict[str, str] = {
    "int": "CAST(vpv.property_value AS INTEGER)",
    "float": "CAST(vpv.property_value AS REAL)",
    "bool": "vpv.property_value",  # stored as "0"/"1"
    "str": "vpv.property_value",
}


def properties_to_field_types(
    properties: dict[str, PropertyMeta],
) -> dict[str, FieldType | SetType]:
    """Convert PropertyMeta dict to ExpressionParser properties config."""
    _type_map = {
        "bool": FieldType.BOOL,
        "int": FieldType.INT,
        "float": FieldType.FLOAT,
        "str": FieldType.STR,
    }
    return {
        name: _type_map[meta.type].as_set if meta.multiple else _type_map[meta.type]
        for name, meta in properties.items()
    }


# ── Compiler ───────────────────────────────────────────────────────────


class SqlExpressionCompiler:
    """Compile searchexp IR nodes to SQL WHERE clause fragments."""

    __slots__ = ("_properties",)

    def __init__(self, *, properties: dict[str, PropertyMeta] | None = None):
        self._properties = properties or {}

    def compile(self, node: Node) -> SqlFragment:
        return self._compile(node)

    # ── Node dispatch ──────────────────────────────────────────────

    def _compile(self, node: Node) -> SqlFragment:
        if isinstance(node, FieldRef):
            return self._compile_field_ref(node)
        if isinstance(node, LiteralValue):
            return self._compile_literal(node)
        if isinstance(node, SetLiteral):
            return self._compile_set_literal(node)
        if isinstance(node, FunctionCall):
            return self._compile_function_call(node)
        if isinstance(node, Comparison):
            return self._compile_comparison(node)
        if isinstance(node, IsOp):
            return self._compile_is_op(node)
        if isinstance(node, InOp):
            return self._compile_in_op(node)
        if isinstance(node, LogicalOp):
            return self._compile_logical_op(node)
        if isinstance(node, NotOp):
            return self._compile_not_op(node)
        raise TypeError(f"Unknown node type: {type(node).__name__}")

    # ── Leaves ─────────────────────────────────────────────────────

    def _compile_field_ref(self, node: FieldRef) -> SqlFragment:
        if node.source == "property":
            # Bare boolean property → EXISTS check for truthy value
            return self._property_bool_exists(node.name, True)
        if node.name in SET_FIELD_MAP:
            raise TypeError(
                f"Set field '{node.name}' cannot appear as a bare expression"
            )
        sql = ATTRIBUTE_SQL_MAP.get(node.name)
        if sql is None:
            raise TypeError(f"Unknown attribute: '{node.name}'")
        return sql, []

    def _compile_literal(self, node: LiteralValue) -> SqlFragment:
        val = node.value
        if isinstance(val, DateLiteral):
            return "?", [_date_literal_to_timestamp(val)]
        if isinstance(val, DateTimestamp):
            return "?", [val.value]
        if isinstance(val, bool):
            return "?", [int(val)]
        return "?", [val]

    def _compile_set_literal(self, node: SetLiteral) -> SqlFragment:
        params: list[Any] = []
        placeholders: list[str] = []
        for elem in node.elements:
            _, p = self._compile_literal(elem)
            params.extend(p)
            placeholders.append("?")
        return f"({', '.join(placeholders)})", params

    # ── Operators ──────────────────────────────────────────────────

    def _compile_comparison(self, node: Comparison) -> SqlFragment:
        # Property on either side → EXISTS subquery
        if isinstance(node.left, FieldRef) and node.left.source == "property":
            return self._property_comparison(node.left, node.op, node.right)
        if isinstance(node.right, FieldRef) and node.right.source == "property":
            return self._property_comparison(
                node.right, _reverse_op(node.op), node.left
            )
        left_sql, left_p = self._compile(node.left)
        right_sql, right_p = self._compile(node.right)
        sql_op = "=" if node.op == "==" else ("!=" if node.op == "!=" else node.op)
        return f"{left_sql} {sql_op} {right_sql}", left_p + right_p

    def _compile_is_op(self, node: IsOp) -> SqlFragment:
        if isinstance(node.left, FieldRef) and node.left.source == "property":
            return self._property_bool_exists(node.left.name, node.value)
        left_sql, left_p = self._compile(node.left)
        return f"{left_sql} = ?", left_p + [int(node.value)]

    def _compile_in_op(self, node: InOp) -> SqlFragment:
        neg = node.negated
        right = node.right

        # "val" in set_attribute (e.g., "eng" in audio_languages)
        if isinstance(right, FieldRef) and isinstance(right.field_type, SetType):
            if right.source == "property":
                return self._property_set_in(node.left, right.name, neg)
            return self._set_field_in(node.left, right.name, neg)

        # "val" in string_field (substring)
        if isinstance(right, FieldRef) and right.field_type == FieldType.STR:
            if right.source == "property":
                return self._property_str_contains(node.left, right.name, neg)
            right_sql, right_p = self._compile(right)
            left_sql, left_p = self._compile(node.left)
            op = "=" if neg else ">"
            return f"INSTR({right_sql}, {left_sql}) {op} 0", right_p + left_p

        # field in {set_literal}
        if isinstance(right, SetLiteral):
            if not right.elements:
                return ("0" if not neg else "1"), []
            left_sql, left_p = self._compile(node.left)
            right_sql, right_p = self._compile_set_literal(right)
            prefix = "NOT " if neg else ""
            return f"{prefix}{left_sql} IN {right_sql}", left_p + right_p

        left_sql, left_p = self._compile(node.left)
        right_sql, right_p = self._compile(right)
        prefix = "NOT " if neg else ""
        return f"{prefix}{left_sql} IN {right_sql}", left_p + right_p

    def _compile_logical_op(self, node: LogicalOp) -> SqlFragment:
        left_sql, left_p = self._compile(node.left)
        right_sql, right_p = self._compile(node.right)
        if node.op == "xor":
            # (A AND NOT B) OR (NOT A AND B)
            return (
                f"(({left_sql}) AND NOT ({right_sql})) "
                f"OR (NOT ({left_sql}) AND ({right_sql}))",
                left_p + right_p + left_p + right_p,
            )
        sql_op = node.op.upper()
        return f"({left_sql}) {sql_op} ({right_sql})", left_p + right_p

    def _compile_not_op(self, node: NotOp) -> SqlFragment:
        sql, params = self._compile(node.operand)
        return f"NOT ({sql})", params

    def _compile_function_call(self, node: FunctionCall) -> SqlFragment:
        assert node.name == "len"
        arg = node.arg
        if isinstance(arg, FieldRef):
            # len(set_attribute)
            if arg.name in SET_FIELD_MAP:
                m = SET_FIELD_MAP[arg.name]
                filt = f" AND {m.extra_filter}" if m.extra_filter else ""
                return (
                    f"(SELECT COUNT(*) FROM {m.table} "
                    f"WHERE video_id = v.video_id{filt})",
                    [],
                )
            # len(property_set)
            if arg.source == "property":
                return (
                    "(SELECT COUNT(*) FROM video_property_value vpv "
                    "JOIN property p ON vpv.property_id = p.property_id "
                    "WHERE vpv.video_id = v.video_id AND p.name = ?)",
                    [arg.name],
                )
            # len(string_attribute)
            sql, params = self._compile_field_ref(arg)
            return f"LENGTH({sql})", params
        sql, params = self._compile(arg)
        return f"LENGTH({sql})", params

    # ── Set-field helpers ──────────────────────────────────────────

    def _set_field_in(self, left: Node, field_name: str, negated: bool) -> SqlFragment:
        m = SET_FIELD_MAP[field_name]
        _, left_p = self._compile(left)
        filt = f" AND {m.extra_filter}" if m.extra_filter else ""
        prefix = "NOT " if negated else ""
        return (
            f"{prefix}EXISTS ("
            f"SELECT 1 FROM {m.table} "
            f"WHERE video_id = v.video_id{filt} AND {m.column} = ?)",
            left_p,
        )

    # ── Property helpers ───────────────────────────────────────────

    def _get_property(self, name: str) -> PropertyMeta:
        if name not in self._properties:
            raise TypeError(f"Unknown property: '{name}'")
        return self._properties[name]

    def _property_cast(self, prop: PropertyMeta) -> str:
        return _PROPERTY_CAST[prop.type]

    def _property_comparison(
        self, field: FieldRef, op: ComparisonOp, other: Node
    ) -> SqlFragment:
        prop = self._get_property(field.name)
        cast_expr = self._property_cast(prop)
        _, other_p = self._compile(other)
        sql_op = "=" if op == "==" else ("!=" if op == "!=" else op)
        return (
            "EXISTS ("
            "SELECT 1 FROM video_property_value vpv "
            "JOIN property p ON vpv.property_id = p.property_id "
            f"WHERE vpv.video_id = v.video_id AND p.name = ? "
            f"AND {cast_expr} {sql_op} ?)",
            [field.name] + other_p,
        )

    def _property_bool_exists(self, name: str, value: bool) -> SqlFragment:
        self._get_property(name)  # validate
        return (
            "EXISTS ("
            "SELECT 1 FROM video_property_value vpv "
            "JOIN property p ON vpv.property_id = p.property_id "
            "WHERE vpv.video_id = v.video_id AND p.name = ? "
            "AND vpv.property_value = ?)",
            [name, str(int(value))],
        )

    def _property_set_in(
        self, left: Node, prop_name: str, negated: bool
    ) -> SqlFragment:
        self._get_property(prop_name)  # validate
        _, left_p = self._compile(left)
        prefix = "NOT " if negated else ""
        return (
            f"{prefix}EXISTS ("
            "SELECT 1 FROM video_property_value vpv "
            "JOIN property p ON vpv.property_id = p.property_id "
            "WHERE vpv.video_id = v.video_id AND p.name = ? "
            "AND vpv.property_value = ?)",
            [prop_name] + left_p,
        )

    def _property_str_contains(
        self, left: Node, prop_name: str, negated: bool
    ) -> SqlFragment:
        self._get_property(prop_name)  # validate
        _, left_p = self._compile(left)
        prefix = "NOT " if negated else ""
        return (
            f"{prefix}EXISTS ("
            "SELECT 1 FROM video_property_value vpv "
            "JOIN property p ON vpv.property_id = p.property_id "
            "WHERE vpv.video_id = v.video_id AND p.name = ? "
            "AND INSTR(vpv.property_value, ?) > 0)",
            [prop_name] + left_p,
        )


# ── Utilities ──────────────────────────────────────────────────────────


def _date_literal_to_timestamp(date: DateLiteral) -> float:
    return UDT(
        date.year,
        date.month or 1,
        date.day or 1,
        date.hour or 0,
        date.minute or 0,
        date.second or 0,
    ).timestamp()


def _reverse_op(op: ComparisonOp) -> ComparisonOp:
    match op:
        case "<":
            return ">"
        case "<=":
            return ">="
        case ">":
            return "<"
        case ">=":
            return "<="
        case "==" | "!=":
            return op
