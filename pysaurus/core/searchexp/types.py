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
    SET = "set"


@dataclass(frozen=True, slots=True)
class FieldRef:
    name: str
    source: Literal["attribute", "property"]
    field_type: FieldType


@dataclass(frozen=True, slots=True)
class LiteralValue:
    value: bool | int | float | str
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
