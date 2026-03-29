from typing import Any, Callable, Self

from pysaurus.core.pythonsearchexp.evaluator import ExpressionEvaluator
from pysaurus.core.searchexp import (
    FieldType,
    SetType,
    ExpressionParser,
    fields_from_class,
    Node,
    DateLiteral,
)


class PythonSearchExp:
    __slots__ = ["_parser", "_evaluator", "_ir_cache"]

    def __init__(
        self,
        *,
        attributes: dict[str, FieldType | SetType] | None = None,
        properties: dict[str, FieldType | SetType] | None = None,
        get_attribute: Callable[[Any, str], Any] | None = None,
        get_property: Callable[[Any, str], Any] | None = None,
        date_to_timestamp: Callable[[DateLiteral], float] | None = None,
    ):
        self._parser = ExpressionParser(attributes=attributes, properties=properties)
        self._evaluator = ExpressionEvaluator(
            get_attribute=get_attribute,
            get_property=get_property,
            date_to_timestamp=date_to_timestamp,
        )
        self._ir_cache: dict[str, Node] = {}

    def _get_ir(self, expr: str) -> Node:
        expr = expr.strip()
        if expr not in self._ir_cache:
            self._ir_cache[expr] = self._parser.parse(expr)
        return self._ir_cache[expr]

    @classmethod
    def from_class(
        cls,
        *,
        class_: type,
        type_mapping: dict[type, FieldType] | None = None,
        exclude: set[str] | None = None,
        properties: dict[str, FieldType | SetType] | None = None,
        get_property: Callable[[Any, str], Any] | None = None,
        date_to_timestamp: Callable[[DateLiteral], float] | None = None,
    ) -> Self:
        return cls(
            attributes=fields_from_class(
                class_, type_mapping=type_mapping, exclude=exclude
            ),
            properties=properties,
            get_property=get_property,
            date_to_timestamp=date_to_timestamp,
        )

    def evaluate(self, expr: str, element: Any) -> bool:
        return self._evaluator.evaluate(self._get_ir(expr), element)
