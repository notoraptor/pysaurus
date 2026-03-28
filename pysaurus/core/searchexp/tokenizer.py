from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # Literals
    NUMBER = auto()
    DURATION = auto()
    DATE = auto()
    STRING = auto()
    # Identifiers and properties
    IDENT = auto()
    PROPERTY = auto()
    # Keywords
    AND = auto()
    OR = auto()
    XOR = auto()
    NOT = auto()
    IN = auto()
    IS = auto()
    TRUE = auto()
    FALSE = auto()
    LEN = auto()
    # Comparison operators
    EQ = auto()
    NEQ = auto()
    LT = auto()
    LTE = auto()
    GT = auto()
    GTE = auto()
    # Punctuation
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    # End
    EOF = auto()


@dataclass(frozen=True, slots=True)
class Token:
    type: TokenType
    value: str
    position: int


_KEYWORDS = {
    "and": TokenType.AND,
    "or": TokenType.OR,
    "xor": TokenType.XOR,
    "not": TokenType.NOT,
    "in": TokenType.IN,
    "is": TokenType.IS,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "len": TokenType.LEN,
}

_OPERATORS = [
    ("==", TokenType.EQ),
    ("!=", TokenType.NEQ),
    ("<=", TokenType.LTE),
    (">=", TokenType.GTE),
    ("<", TokenType.LT),
    (">", TokenType.GT),
    ("(", TokenType.LPAREN),
    (")", TokenType.RPAREN),
    ("{", TokenType.LBRACE),
    ("}", TokenType.RBRACE),
    (",", TokenType.COMMA),
]

# Duration suffixes ordered by decreasing precision rank.
# Order matters: longest match first (min before m).
_DURATION_SUFFIXES = ("d", "h", "min", "s", "u")
_DURATION_RANKS = {s: i for i, s in enumerate(_DURATION_SUFFIXES)}

# Multiplier suffixes — longest match first (gi before g, etc.)
_MULTIPLIERS = {
    "ki": 1024,
    "mi": 1048576,
    "gi": 1073741824,
    "ti": 1099511627776,
    "k": 1000,
    "m": 1000000,
    "g": 1000000000,
    "t": 1000000000000,
}

# Regex for a duration: digits followed by a duration suffix, repeated.
# We validate ordering after matching.
_RE_DURATION_PART = re.compile(r"(\d+)(d|h|min|s|u)", re.IGNORECASE)

_RE_WS = re.compile(r"\s+")
_RE_IDENT = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")

# Date pattern: YYYY-MM(-DD(THH(:MM(:SS)?)?)?)?
# YYYY alone is handled as NUMBER (ambiguous, resolved at typing).
_RE_DATE = re.compile(
    r"\d{4}-\d{2}"
    r"(?:-\d{2}"
    r"(?:T\d{2}"
    r"(?::\d{2}"
    r"(?::\d{2})?"
    r")?"
    r")?"
    r")?"
)


def _try_tokenize_number_or_duration(source: str, pos: int) -> Token | None:
    """Try to tokenize a number (with optional multiplier) or a duration."""
    # Collect the full run of digits, dots, and alpha suffix characters
    # to determine whether this is a duration, a number with multiplier,
    # or a plain number.
    start = pos
    i = pos

    # First, try to match as duration (greedy: match all duration parts)
    parts = []
    j = i
    while j < len(source):
        m = _RE_DURATION_PART.match(source, j)
        if m and m.start() == j:
            suffix = m.group(2).lower()
            parts.append((m.group(1), suffix, m.start()))
            j = m.end()
        else:
            break

    if parts:
        # Check that nothing else follows immediately (no letter/digit)
        if j < len(source) and (source[j].isalnum() or source[j] == "_"):
            # Not a valid duration — fall through to number parsing
            pass
        else:
            # Validate ordering: must be strictly decreasing rank
            for k in range(1, len(parts)):
                prev_rank = _DURATION_RANKS[parts[k - 1][1]]
                curr_rank = _DURATION_RANKS[parts[k][1]]
                if curr_rank <= prev_rank:
                    from .errors import ExpressionError

                    raise ExpressionError(
                        f"Duration components must be in decreasing order"
                        f" ('{parts[k][1]}' after '{parts[k - 1][1]}')",
                        parts[k][2],
                        len(parts[k][0]) + len(parts[k][1]),
                    )
            # Check no duplicate suffixes
            # (Defensive: ordering check above already catches duplicates
            # since equal ranks fail the strictly-decreasing constraint.)
            seen = set()
            for digits, suffix, p in parts:
                if suffix in seen:  # pragma: no cover
                    from .errors import ExpressionError

                    raise ExpressionError(
                        f"Duplicate duration component '{suffix}'",
                        p,
                        len(digits) + len(suffix),
                    )
                seen.add(suffix)
            raw = source[start:j]
            return Token(TokenType.DURATION, raw, start)

    # Not a duration — try date or number
    i = pos
    while i < len(source) and source[i].isdigit():
        i += 1
    if i == pos:  # pragma: no cover — caller guarantees source[pos].isdigit()
        return None

    # Try date: exactly 4 digits followed by '-'
    digit_count = i - pos
    if digit_count == 4 and i < len(source) and source[i] == "-":
        m = _RE_DATE.match(source, pos)
        if m:
            raw = m.group()
            # Ensure not followed by more alnum (would be invalid)
            end = m.end()
            if end >= len(source) or not (source[end].isalnum() or source[end] == "_"):
                return Token(TokenType.DATE, raw, pos)

    if (
        i < len(source)
        and source[i] == "."
        and i + 1 < len(source)
        and source[i + 1].isdigit()
    ):
        i += 1  # skip dot
        while i < len(source) and source[i].isdigit():
            i += 1

    # Check for multiplier suffix
    rest = source[i:]
    rest_lower = rest[:2].lower()
    # Try 2-char suffixes first, then 1-char
    for suffix in ("ki", "mi", "gi", "ti", "k", "m", "g", "t"):
        if rest_lower.startswith(suffix):
            # Make sure it's not followed by more identifier chars
            end = i + len(suffix)
            if end < len(source) and (source[end].isalnum() or source[end] == "_"):
                # Could be a duration suffix like "min" — check
                if (
                    suffix == "m"
                    and rest_lower.startswith("mi")
                    and not rest_lower.startswith("min")
                ):
                    continue
                if (
                    suffix == "m" and len(rest) >= 3 and rest[:3].lower() == "min"
                ):  # pragma: no cover
                    # This is actually a duration suffix, not multiplier
                    # (Defensive: the "mi" check above catches this case first
                    # since rest_lower is only 2 chars and "mi" ⊂ "min".)
                    return None
                continue
            i = end
            break

    # Verify nothing follows immediately (no letters/digits)
    if i < len(source) and (source[i].isalpha() or source[i] == "_"):
        # Something unexpected follows — this might be part of an identifier
        # or a duration we failed to parse. Reset.
        return None

    raw = source[start:i]
    return Token(TokenType.NUMBER, raw, start)


def tokenize(source: str) -> list[Token]:
    """Tokenize an expression string into a list of tokens."""
    from .errors import ExpressionError

    tokens: list[Token] = []
    pos = 0
    length = len(source)

    while pos < length:
        # Skip whitespace
        m = _RE_WS.match(source, pos)
        if m:
            pos = m.end()
            continue

        # String literals
        if source[pos] in ('"', "'"):
            quote = source[pos]
            start = pos
            pos += 1
            while pos < length and source[pos] != quote:
                pos += 1
            if pos >= length:
                raise ExpressionError("Unterminated string literal", start, pos - start)
            pos += 1  # closing quote
            tokens.append(Token(TokenType.STRING, source[start:pos], start))
            continue

        # Property (backtick-delimited)
        if source[pos] == "`":
            start = pos
            pos += 1
            while pos < length and source[pos] != "`":
                pos += 1
            if pos >= length:
                raise ExpressionError("Unterminated property name", start, pos - start)
            pos += 1  # closing backtick
            content = source[start + 1 : pos - 1]
            if not content:
                raise ExpressionError("Empty property name", start, 2)
            tokens.append(Token(TokenType.PROPERTY, content, start))
            continue

        # Number or duration (must try before operators because of potential
        # leading digits)
        if source[pos].isdigit():
            tok = _try_tokenize_number_or_duration(source, pos)
            if tok:
                tokens.append(tok)
                pos = tok.position + len(tok.value)
                continue
            # If we got here, digits were followed by something unexpected
            raise ExpressionError("Invalid numeric literal", pos, 1)

        # Operators and punctuation (try longest match first — 2-char then 1-char)
        matched = False
        for op_str, op_type in _OPERATORS:
            if source[pos : pos + len(op_str)] == op_str:
                tokens.append(Token(op_type, op_str, pos))
                pos += len(op_str)
                matched = True
                break
        if matched:
            continue

        # Identifier or keyword
        m = _RE_IDENT.match(source, pos)
        if m:
            word = m.group()
            kw = _KEYWORDS.get(word.lower())
            if kw:
                tokens.append(Token(kw, word, m.start()))
            else:
                tokens.append(Token(TokenType.IDENT, word, m.start()))
            pos = m.end()
            continue

        raise ExpressionError(f"Unexpected character '{source[pos]}'", pos)

    tokens.append(Token(TokenType.EOF, "", length))
    return tokens


def parse_number(value: str) -> int | float:
    """Parse a NUMBER token value into its numeric value."""
    lower = value.lower()
    # Check for multiplier suffix
    for suffix in ("ki", "mi", "gi", "ti", "k", "m", "g", "t"):
        if lower.endswith(suffix):
            num_part = value[: len(value) - len(suffix)]
            base = float(num_part) if "." in num_part else int(num_part)
            result = base * _MULTIPLIERS[suffix]
            if isinstance(result, float) and result == int(result):
                return int(result)
            return result
    if "." in value:
        return float(value)
    return int(value)


def parse_duration_microseconds(value: str) -> int:
    """Parse a DURATION token value into microseconds."""
    total = 0
    factors = {
        "d": 86400_000_000,
        "h": 3600_000_000,
        "min": 60_000_000,
        "s": 1_000_000,
        "u": 1,
    }
    for m in _RE_DURATION_PART.finditer(value):
        digits = int(m.group(1))
        suffix = m.group(2).lower()
        total += digits * factors[suffix]
    return total
