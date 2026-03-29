from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class FieldType(Enum):
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STR = "str"
    DATE = "date"
    DURATION = "duration"
    FILESIZE = "filesize"

    @property
    def as_set(self) -> SetType:
        """Return a SetType with this field type as element type."""
        return SetType(self)


@dataclass(frozen=True, slots=True)
class SetType:
    """A set field with a known element type."""

    element_type: FieldType

    def __str__(self) -> str:
        return f"set[{self.element_type.value}]"


@dataclass(frozen=True, slots=True)
class DateLiteral:
    """Date as parsed components, without timezone interpretation."""

    year: int
    month: int | None = None
    day: int | None = None
    hour: int | None = None
    minute: int | None = None
    second: int | None = None


@dataclass(frozen=True, slots=True)
class DateTimestamp:
    """Date as a raw Unix timestamp (seconds since epoch)."""

    value: float


@dataclass(frozen=True, slots=True)
class FieldRef:
    name: str
    source: Literal["attribute", "property"]
    field_type: FieldType | SetType


@dataclass(frozen=True, slots=True)
class LiteralValue:
    value: bool | int | float | str | DateLiteral | DateTimestamp
    field_type: FieldType


@dataclass(frozen=True, slots=True)
class SetLiteral:
    elements: tuple[LiteralValue, ...]
    element_type: FieldType


@dataclass(frozen=True, slots=True)
class FunctionCall:
    name: str
    arg: Node
    result_type: FieldType


ComparisonOp = Literal["==", "!=", "<", "<=", ">", ">="]


@dataclass(frozen=True, slots=True)
class Comparison:
    left: Node
    op: ComparisonOp
    right: Node


@dataclass(frozen=True, slots=True)
class IsOp:
    left: Node
    value: bool


@dataclass(frozen=True, slots=True)
class InOp:
    left: Node
    right: Node
    negated: bool


@dataclass(frozen=True, slots=True)
class LogicalOp:
    left: Node
    op: Literal["and", "or", "xor"]
    right: Node


@dataclass(frozen=True, slots=True)
class NotOp:
    operand: Node


Node = (
    FieldRef
    | LiteralValue
    | SetLiteral
    | FunctionCall
    | Comparison
    | IsOp
    | InOp
    | LogicalOp
    | NotOp
)
