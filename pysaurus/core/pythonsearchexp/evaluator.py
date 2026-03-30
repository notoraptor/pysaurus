from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pysaurus.core.universal_datetime import UDT

from pysaurus.core.searchexp.types import (
    Comparison,
    ComparisonOp,
    DateLiteral,
    DateTimestamp,
    FieldRef,
    FunctionCall,
    InOp,
    IsOp,
    LiteralValue,
    LogicalOp,
    Node,
    NotOp,
    SetLiteral,
)


class ExpressionEvaluator:
    """Evaluate parsed expressions against objects. Independent of Pysaurus.

    The caller provides getter functions for field access and a date
    converter. Getters must return raw comparable values (float for dates,
    int for durations/sizes, set for collection fields).
    """

    __slots__ = ("_get_attribute", "_get_property", "_date_to_timestamp")

    def __init__(
        self,
        *,
        get_attribute: Callable[[Any, str], Any] | None = None,
        get_property: Callable[[Any, str], Any] | None = None,
        date_to_timestamp: Callable[[DateLiteral], float] | None = None,
    ):
        self._get_attribute = get_attribute or getattr
        self._get_property = get_property
        self._date_to_timestamp = date_to_timestamp or _default_date_to_timestamp

    def evaluate(self, node: Node, obj: Any) -> bool:
        """Evaluate a parsed expression against an object."""
        return bool(self._eval(node, obj))

    def _eval(self, node: Node, obj: Any) -> Any:
        if isinstance(node, FieldRef):
            return self._eval_field(node, obj)
        if isinstance(node, LiteralValue):
            return self._resolve_literal(node)
        if isinstance(node, SetLiteral):
            return frozenset(self._resolve_literal(e) for e in node.elements)
        if isinstance(node, FunctionCall):
            return len(self._eval(node.arg, obj))
        if isinstance(node, Comparison):
            return _compare(
                self._eval(node.left, obj), node.op, self._eval(node.right, obj)
            )
        if isinstance(node, IsOp):
            return self._eval(node.left, obj) == node.value
        if isinstance(node, InOp):
            result = self._eval(node.left, obj) in self._eval(node.right, obj)
            return not result if node.negated else result
        if isinstance(node, LogicalOp):
            return self._eval_logical(node, obj)
        if isinstance(node, NotOp):
            return not self._eval(node.operand, obj)
        raise TypeError(f"Unknown node type: {type(node).__name__}")

    def _eval_field(self, node: FieldRef, obj: Any) -> Any:
        if node.source == "attribute":
            return self._get_attribute(obj, node.name)
        if self._get_property is None:
            raise TypeError(f"No property getter configured (needed for '{node.name}')")
        return self._get_property(obj, node.name)

    def _resolve_literal(self, node: LiteralValue) -> bool | int | float | str:
        val = node.value
        if isinstance(val, DateLiteral):
            return self._date_to_timestamp(val)
        if isinstance(val, DateTimestamp):
            return val.value
        return val

    def _eval_logical(self, node: LogicalOp, obj: Any) -> bool:
        left = self._eval(node.left, obj)
        if node.op == "and":
            return bool(left and self._eval(node.right, obj))
        if node.op == "or":
            return bool(left or self._eval(node.right, obj))
        right = self._eval(node.right, obj)
        return bool(left) ^ bool(right)


def _compare(left: Any, op: ComparisonOp, right: Any) -> bool:
    match op:
        case "==":
            return bool(left == right)
        case "!=":
            return bool(left != right)
        case "<":
            return bool(left < right)
        case "<=":
            return bool(left <= right)
        case ">":
            return bool(left > right)
        case ">=":
            return bool(left >= right)


def _default_date_to_timestamp(date: DateLiteral) -> float:
    return UDT(
        date.year,
        date.month or 1,
        date.day or 1,
        date.hour or 0,
        date.minute or 0,
        date.second or 0,
    ).timestamp()
