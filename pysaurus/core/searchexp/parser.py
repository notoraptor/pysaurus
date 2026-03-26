from __future__ import annotations

from datetime import datetime
from typing import cast

from .errors import ExpressionError
from .tokenizer import (
    Token,
    TokenType,
    parse_duration_microseconds,
    parse_number,
    tokenize,
)
from .types import (
    Comparison,
    ComparisonOp,
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
)

# Types that support ordering comparisons (<, <=, >, >=)
_ORDERABLE = {
    FieldType.INT,
    FieldType.FLOAT,
    FieldType.STR,
    FieldType.DATE,
    FieldType.DURATION,
    FieldType.FILESIZE,
}

# Cross-compatibility groups for numeric types
_COMPAT_GROUPS: dict[FieldType, int] = {
    FieldType.INT: 0,
    FieldType.FLOAT: 0,
    FieldType.DATE: 1,
    FieldType.DURATION: 2,
    FieldType.FILESIZE: 3,
}


def _types_compatible(a: FieldType, b: FieldType) -> bool:
    if a == b:
        return True
    if a in _COMPAT_GROUPS and b in _COMPAT_GROUPS:
        ga, gb = _COMPAT_GROUPS[a], _COMPAT_GROUPS[b]
        # int/float (group 0) are compatible with any numeric group
        if ga == 0 or gb == 0:
            return True
    return False


def _date_to_timestamp(text: str) -> float:
    """Convert a date string to a Unix timestamp (local time).

    Uses local time to match ``Date.__str__`` (which displays via
    ``datetime.fromtimestamp``), so the user sees consistent dates.
    """
    formats = [
        ("%Y", 4),
        ("%Y-%m", 7),
        ("%Y-%m-%d", 10),
        ("%Y-%m-%dT%H", 13),
        ("%Y-%m-%dT%H:%M", 16),
        ("%Y-%m-%dT%H:%M:%S", 19),
    ]
    for fmt, expected_len in formats:
        if len(text) == expected_len:
            dt = datetime.strptime(text, fmt)
            return dt.timestamp()
    raise ValueError(f"Invalid date format: {text}")


def _is_date_shaped(text: str) -> bool:
    """Check if a NUMBER token could be a date (4-digit year)."""
    return len(text) == 4 and text.isdigit() and 1000 <= int(text) <= 9999


class ExpressionParser:
    """Expression search parser. Independent of Pysaurus."""

    def __init__(
        self,
        *,
        attributes: dict[str, FieldType] | None = None,
        properties: dict[str, FieldType] | None = None,
    ):
        if not attributes and not properties:
            raise ValueError(
                "At least one of 'attributes' or 'properties' must be provided"
            )
        self._attributes = dict(attributes) if attributes else {}
        self._properties = dict(properties) if properties else {}

    def parse(self, expression: str) -> Node:
        """Parse and validate an expression, returning an AST."""
        tokens = tokenize(expression)
        parser = _Parser(tokens, self._attributes, self._properties)
        node = parser.parse_expression()
        parser.expect(TokenType.EOF)
        _check_boolean_context(node)
        return node


def _check_boolean_context(node: Node) -> None:
    """Verify that the root node produces a boolean result."""
    if isinstance(node, FieldRef):
        if node.field_type != FieldType.BOOL:
            raise ExpressionError(
                f"Field '{node.name}' ({node.field_type.value}) used as boolean"
                f" — use a comparison operator",
                0,
            )
    elif isinstance(node, (LiteralValue, SetLiteral)):
        raise ExpressionError("A literal alone is not a valid expression", 0)
    elif isinstance(node, FunctionCall):
        raise ExpressionError(
            "Function call alone is not a valid expression — use a comparison operator",
            0,
        )


class _Parser:
    __slots__ = ("_tokens", "_pos", "_attributes", "_properties")

    def __init__(
        self,
        tokens: list[Token],
        attributes: dict[str, FieldType],
        properties: dict[str, FieldType],
    ):
        self._tokens = tokens
        self._pos = 0
        self._attributes = attributes
        self._properties = properties

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _match(self, *types: TokenType) -> Token | None:
        if self._peek().type in types:
            return self._advance()
        return None

    def expect(self, token_type: TokenType) -> Token:
        tok = self._peek()
        if tok.type != token_type:
            raise ExpressionError(
                f"Expected {token_type.name}, got '{tok.value}'",
                tok.position,
                max(len(tok.value), 1),
            )
        return self._advance()

    def parse_expression(self) -> Node:
        return self._parse_or()

    def _parse_or(self) -> Node:
        left = self._parse_xor()
        while self._match(TokenType.OR):
            right = self._parse_xor()
            _ensure_boolean_operands(left, right, "or")
            left = LogicalOp(left, "or", right)
        return left

    def _parse_xor(self) -> Node:
        left = self._parse_and()
        while self._match(TokenType.XOR):
            right = self._parse_and()
            _ensure_boolean_operands(left, right, "xor")
            left = LogicalOp(left, "xor", right)
        return left

    def _parse_and(self) -> Node:
        left = self._parse_not()
        while self._match(TokenType.AND):
            right = self._parse_not()
            _ensure_boolean_operands(left, right, "and")
            left = LogicalOp(left, "and", right)
        return left

    def _parse_not(self) -> Node:
        tok = self._match(TokenType.NOT)
        if tok:
            # Check for "not in" — if next is IN, this is handled at comparison level
            if self._peek().type == TokenType.IN:
                # Back up — let comparison handle "not in"
                self._pos -= 1
                return self._parse_comparison()
            operand = self._parse_not()
            return NotOp(operand)
        return self._parse_comparison()

    def _parse_comparison(self) -> Node:
        left = self._parse_operand()
        tok = self._peek()

        # comp_op: ==, !=, <, <=, >, >=
        comp_ops = {
            TokenType.EQ: "==",
            TokenType.NEQ: "!=",
            TokenType.LT: "<",
            TokenType.LTE: "<=",
            TokenType.GT: ">",
            TokenType.GTE: ">=",
        }
        if tok.type in comp_ops:
            op_tok = self._advance()
            op_str = comp_ops[op_tok.type]
            right = self._parse_operand()
            return self._resolve_comparison(left, op_str, right, op_tok)

        # IS [NOT] boolean
        if tok.type == TokenType.IS:
            self._advance()
            negated = bool(self._match(TokenType.NOT))
            bool_tok = self._peek()
            if bool_tok.type == TokenType.TRUE:
                self._advance()
                value = not negated
            elif bool_tok.type == TokenType.FALSE:
                self._advance()
                value = negated
            else:
                raise ExpressionError(
                    "Expected True or False after 'is'",
                    bool_tok.position,
                    max(len(bool_tok.value), 1),
                )
            left = _resolve_field_or_fail(left, tok)
            if _node_type(left) != FieldType.BOOL:
                raise ExpressionError(
                    "'is' operator requires a boolean field", tok.position, 2
                )
            return IsOp(left, value)

        # [NOT] IN
        if tok.type == TokenType.NOT:
            next_tok = (
                self._tokens[self._pos + 1]
                if self._pos + 1 < len(self._tokens)
                else None
            )
            if next_tok and next_tok.type == TokenType.IN:
                self._advance()  # consume NOT
                self._advance()  # consume IN
                right = self._parse_operand()
                return self._resolve_in(left, right, negated=True, op_tok=tok)

        if tok.type == TokenType.IN:
            self._advance()
            right = self._parse_operand()
            return self._resolve_in(left, right, negated=False, op_tok=tok)

        return left

    def _parse_operand(self) -> Node:
        if self._peek().type == TokenType.LEN:
            return self._parse_function_call()
        return self._parse_atom()

    def _parse_function_call(self) -> Node:
        func_tok = self.expect(TokenType.LEN)
        self.expect(TokenType.LPAREN)
        arg = self._parse_operand()
        self.expect(TokenType.RPAREN)
        arg = _resolve_field_or_fail(arg, func_tok)
        arg_type = _node_type(arg)
        if arg_type not in (FieldType.STR, FieldType.SET):
            raise ExpressionError(
                f"len() requires str or set, got {arg_type.value}", func_tok.position, 3
            )
        return FunctionCall("len", arg, FieldType.INT)

    def _parse_atom(self) -> Node:
        tok = self._peek()

        if tok.type == TokenType.IDENT:
            self._advance()
            if tok.value not in self._attributes:
                suffix = "" if self._attributes else " (no attributes defined)"
                raise ExpressionError(
                    f"Unknown attribute '{tok.value}'{suffix}",
                    tok.position,
                    len(tok.value),
                )
            return FieldRef(tok.value, "attribute", self._attributes[tok.value])

        if tok.type == TokenType.PROPERTY:
            self._advance()
            if tok.value not in self._properties:
                suffix = "" if self._properties else " (no properties defined)"
                raise ExpressionError(
                    f"Unknown property '{tok.value}'{suffix}",
                    tok.position,
                    len(tok.value) + 2,
                )
            return FieldRef(tok.value, "property", self._properties[tok.value])

        if tok.type == TokenType.NUMBER:
            self._advance()
            return _parse_number_literal(tok)

        if tok.type == TokenType.DATE:
            self._advance()
            ts = _date_to_timestamp(tok.value)
            return LiteralValue(ts, FieldType.DATE)

        if tok.type == TokenType.DURATION:
            self._advance()
            us = parse_duration_microseconds(tok.value)
            return LiteralValue(us, FieldType.DURATION)

        if tok.type == TokenType.STRING:
            self._advance()
            # Strip quotes
            content = tok.value[1:-1]
            return LiteralValue(content, FieldType.STR)

        if tok.type in (TokenType.TRUE, TokenType.FALSE):
            self._advance()
            return LiteralValue(tok.type == TokenType.TRUE, FieldType.BOOL)

        if tok.type == TokenType.LBRACE:
            return self._parse_set_literal()

        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        raise ExpressionError(
            f"Unexpected token '{tok.value}'", tok.position, max(len(tok.value), 1)
        )

    def _parse_set_literal(self) -> Node:
        open_tok = self.expect(TokenType.LBRACE)
        if self._match(TokenType.RBRACE):
            return SetLiteral((), FieldType.STR)

        elements: list[LiteralValue] = []
        first = self._parse_set_element()
        elements.append(first)

        while self._match(TokenType.COMMA):
            if self._peek().type == TokenType.RBRACE:
                break  # trailing comma
            elements.append(self._parse_set_element())

        self.expect(TokenType.RBRACE)

        # Determine element type (all must be same type)
        elem_type = elements[0].field_type
        for elem in elements[1:]:
            if elem.field_type != elem_type:
                if _types_compatible(elem.field_type, elem_type):
                    # Promote to float if mixing int/float
                    if {elem.field_type, elem_type} == {FieldType.INT, FieldType.FLOAT}:
                        elem_type = FieldType.FLOAT
                else:
                    raise ExpressionError(
                        f"Mixed types in set literal:"
                        f" {elem_type.value} and {elem.field_type.value}",
                        open_tok.position,
                    )

        return SetLiteral(tuple(elements), elem_type)

    def _parse_set_element(self) -> LiteralValue:
        tok = self._peek()
        if tok.type == TokenType.NUMBER:
            self._advance()
            return _parse_number_literal(tok)
        if tok.type == TokenType.DATE:
            self._advance()
            ts = _date_to_timestamp(tok.value)
            return LiteralValue(ts, FieldType.DATE)
        if tok.type == TokenType.DURATION:
            self._advance()
            us = parse_duration_microseconds(tok.value)
            return LiteralValue(us, FieldType.DURATION)
        if tok.type == TokenType.STRING:
            self._advance()
            return LiteralValue(tok.value[1:-1], FieldType.STR)
        if tok.type in (TokenType.TRUE, TokenType.FALSE):
            self._advance()
            return LiteralValue(tok.type == TokenType.TRUE, FieldType.BOOL)
        raise ExpressionError(
            f"Expected a literal in set, got '{tok.value}'",
            tok.position,
            max(len(tok.value), 1),
        )

    def _resolve_comparison(
        self, left: Node, op: str, right: Node, op_tok: Token
    ) -> Comparison:
        _check_literal_vs_literal(left, right, op_tok)
        left, right = _resolve_types_binary(left, right, op_tok)
        lt = _node_type(left)
        rt = _node_type(right)

        if not _types_compatible(lt, rt):
            raise ExpressionError(
                f"Cannot compare {lt.value} with {rt.value}",
                op_tok.position,
                len(op_tok.value),
            )

        if op in ("<", "<=", ">", ">="):
            if lt not in _ORDERABLE or rt not in _ORDERABLE:
                raise ExpressionError(
                    f"Operator '{op}' not supported for {lt.value}",
                    op_tok.position,
                    len(op_tok.value),
                )

        return Comparison(left, cast(ComparisonOp, op), right)

    def _resolve_in(
        self, left: Node, right: Node, *, negated: bool, op_tok: Token
    ) -> InOp:
        _check_literal_vs_literal(left, right, op_tok)

        # Resolve field types for ambiguous literals
        left, right = _resolve_types_in(left, right, op_tok)

        lt = _node_type(left)
        rt = _node_type(right)

        # str in str (substring)
        if lt == FieldType.STR and rt == FieldType.STR:
            return InOp(left, right, negated)

        # T in set[T] (membership)
        if rt == FieldType.SET:
            elem_type = _set_element_type(right)
            if elem_type is not None and not _types_compatible(lt, elem_type):
                raise ExpressionError(
                    f"Cannot test {lt.value} membership in set of {elem_type.value}",
                    op_tok.position,
                    len(op_tok.value),
                )
            return InOp(left, right, negated)

        raise ExpressionError(
            f"'in' requires str or set on the right side, got {rt.value}",
            op_tok.position,
            len(op_tok.value),
        )


def _parse_number_literal(tok: Token) -> LiteralValue:
    value = parse_number(tok.value)
    if isinstance(value, float):
        return LiteralValue(value, FieldType.FLOAT)
    return LiteralValue(value, FieldType.INT)


def _node_type(node: Node) -> FieldType:
    if isinstance(node, FieldRef):
        return node.field_type
    if isinstance(node, LiteralValue):
        return node.field_type
    if isinstance(node, SetLiteral):
        return FieldType.SET
    if isinstance(node, FunctionCall):
        return node.result_type
    # Comparison, IsOp, InOp, LogicalOp, NotOp
    return FieldType.BOOL


def _is_literal(node: Node) -> bool:
    return isinstance(node, (LiteralValue, SetLiteral))


def _is_field(node: Node) -> bool:
    return isinstance(node, (FieldRef, FunctionCall))


def _check_literal_vs_literal(left: Node, right: Node, op_tok: Token) -> None:
    if _is_literal(left) and _is_literal(right):
        raise ExpressionError(
            "Both sides of operator are literals"
            " — at least one must be a field or function",
            op_tok.position,
            len(op_tok.value),
        )


def _resolve_field_or_fail(node: Node, context_tok: Token) -> Node:
    if _is_literal(node):
        raise ExpressionError(
            "Expected a field or function, got a literal",
            context_tok.position,
            max(len(context_tok.value), 1),
        )
    return node


def _resolve_types_binary(left: Node, right: Node, op_tok: Token) -> tuple[Node, Node]:
    """Resolve ambiguous literals based on the field on the other side."""
    if _is_field(left) and _is_literal(right):
        right = _coerce_literal(right, _node_type(left), op_tok)
    elif _is_literal(left) and _is_field(right):
        left = _coerce_literal(left, _node_type(right), op_tok)
    # field vs field or already resolved — nothing to do
    return left, right


def _resolve_types_in(left: Node, right: Node, op_tok: Token) -> tuple[Node, Node]:
    """Resolve types for 'in' operator."""
    if _is_field(left) and isinstance(right, SetLiteral):
        # field in {literals} — coerce set elements to field type
        ft = _node_type(left)
        new_elems: list[LiteralValue] = []
        for e in right.elements:
            coerced = cast(LiteralValue, _coerce_literal(e, ft, op_tok))
            if not _types_compatible(coerced.field_type, ft):
                raise ExpressionError(
                    f"Cannot coerce {coerced.field_type.value} to"
                    f" {ft.value} in set literal",
                    op_tok.position,
                    len(op_tok.value),
                )
            new_elems.append(coerced)
        right = SetLiteral(tuple(new_elems), ft)
    elif _is_literal(left) and _is_field(right):
        rt = _node_type(right)
        if rt == FieldType.SET:
            # literal in set_field — we don't know element type at parse time
            # for set fields, so we leave it as-is
            pass
        elif rt == FieldType.STR:
            left = _coerce_literal(left, FieldType.STR, op_tok)
        else:
            left = _coerce_literal(left, rt, op_tok)
    elif _is_field(left) and _is_field(right):
        pass  # both known
    return left, right


def _coerce_literal(node: Node, target: FieldType, _op_tok: Token) -> Node:
    """Coerce a literal node to the target field type."""
    if not isinstance(node, LiteralValue):
        return node

    src = node.field_type
    val = node.value

    if src == target:
        return node

    # INT can be coerced to many types
    if src == FieldType.INT and isinstance(val, int):
        if target == FieldType.FLOAT:
            return LiteralValue(float(val), FieldType.FLOAT)
        if target == FieldType.DATE:
            # Interpret as year if it looks like one
            if _is_date_shaped(str(val)):
                ts = _date_to_timestamp(str(val))
                return LiteralValue(ts, FieldType.DATE)
            # Otherwise treat as raw timestamp
            return LiteralValue(float(val), FieldType.DATE)
        if target == FieldType.DURATION:
            return LiteralValue(val, FieldType.DURATION)
        if target == FieldType.FILESIZE:
            return LiteralValue(val, FieldType.FILESIZE)

    # FLOAT can be coerced to date/duration/filesize
    if src == FieldType.FLOAT and isinstance(val, (int, float)):
        if target == FieldType.INT:
            if val == int(val):
                return LiteralValue(int(val), FieldType.INT)
        if target == FieldType.DATE:
            return LiteralValue(float(val), FieldType.DATE)
        if target == FieldType.DURATION:
            return LiteralValue(val, FieldType.DURATION)
        if target == FieldType.FILESIZE:
            return LiteralValue(val, FieldType.FILESIZE)

    # No valid coercion
    return node


def _set_element_type(node: Node) -> FieldType | None:
    if isinstance(node, SetLiteral):
        return node.element_type
    if isinstance(node, FieldRef) and node.field_type == FieldType.SET:
        return None  # element type unknown for set fields
    return None


def _ensure_boolean_operands(left: Node, right: Node, op: str) -> None:
    """Check that both operands of a logical operator are boolean expressions."""
    for node, side in ((left, "left"), (right, "right")):
        if isinstance(node, FieldRef) and node.field_type != FieldType.BOOL:
            raise ExpressionError(
                f"'{op}' requires boolean operands, but {side} side"
                f" is field '{node.name}' ({node.field_type.value})",
                0,
            )
        if isinstance(node, LiteralValue) and node.field_type != FieldType.BOOL:
            raise ExpressionError(
                f"'{op}' requires boolean operands, but {side} side"
                f" is a {node.field_type.value} literal",
                0,
            )
        if isinstance(node, FunctionCall):
            raise ExpressionError(
                f"'{op}' requires boolean operands, but {side} side"
                f" is a function call returning {node.result_type.value}",
                0,
            )
        if isinstance(node, SetLiteral):
            raise ExpressionError(
                f"'{op}' requires boolean operands, but {side} side is a set literal", 0
            )
