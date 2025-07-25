import itertools
import re
from typing import Iterable


class CharClass:
    __slots__ = "char", "cls", "rank", "lower_rank"
    DIGITS = "0123456789"
    SUP_DIGITS = "\u2070\u00B9\u00B2\u00B3\u2074\u2075\u2076\u2077\u2078\u2079"
    SUB_DIGITS = "\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089"
    CLS_DIG = DIGITS[0]
    CLS_SUP = SUP_DIGITS[0]
    CLS_SUB = SUB_DIGITS[0]
    CLS_ALPHA = "A"

    ORD_0 = ord("0")

    @classmethod
    def parse_sup_digits(cls, text: str) -> int:
        return sum(cls.SUP_DIGITS.find(c) * 10**i for i, c in enumerate(reversed(text)))

    @classmethod
    def parse_sub_digits(cls, text: str) -> int:
        return sum(cls.SUB_DIGITS.find(c) * 10**i for i, c in enumerate(reversed(text)))

    def __init__(self, char: str):
        if char in self.DIGITS:
            cls = self.CLS_DIG
            rnk = self.DIGITS.find(char)
        elif char in self.SUP_DIGITS:
            cls = self.CLS_SUP
            rnk = self.SUP_DIGITS.find(char)
        elif char in self.SUB_DIGITS:
            cls = self.CLS_SUB
            rnk = self.SUB_DIGITS.find(char)
        else:
            cls = self.CLS_ALPHA
            rnk = ord(char)
        self.char = char
        self.cls = cls
        self.rank = rnk
        self.lower_rank = ord(char.lower()) if cls == self.CLS_ALPHA else 0

    def __hash__(self):
        return hash(self.char)

    def __eq__(self, other):
        return self.char == other.char

    def __lt__(self, other):
        return (self.lower_rank - other.lower_rank or self.rank - other.rank) < 0

    def is_digit(self):
        return self.cls != self.CLS_ALPHA

    def is_alpha(self):
        return self.cls == self.CLS_ALPHA


class DigitAccumulator:
    __slots__ = ("_buffer",)

    def __init__(self):
        self._buffer = []

    def append(self, wc: CharClass | None) -> int | None:
        if wc is None or wc.is_alpha():
            if self._buffer:
                return self._flush_buffer_to_number()
            else:
                return None
        elif self._buffer:
            if self._buffer[-1].cls == wc.cls:
                self._buffer.append(wc)
                return None
            else:
                previous_number = self._flush_buffer_to_number()
                self._buffer.append(wc)
                return previous_number
        else:
            self._buffer.append(wc)
            return None

    def _flush_buffer_to_number(self) -> int:
        number = sum(wc.rank * 10**i for i, wc in enumerate(reversed(self._buffer)))
        self._buffer.clear()
        return number


def separate_characters_and_numbers(text: str) -> Iterable[str | int]:
    accumulator = DigitAccumulator()
    for character in text:
        wrapper = CharClass(character)
        number = accumulator.append(wrapper)
        if number is not None:
            yield number
        if wrapper.is_alpha():
            yield character
    number = accumulator.append(None)
    if number is not None:
        yield number


def split_numbers_and_texts(text: str):
    output = []
    accumulator = DigitAccumulator()
    seq = ""
    for character in text:
        wrapper = CharClass(character)
        number = accumulator.append(wrapper)
        if number is not None:
            output.append(number)
        if wrapper.is_alpha():
            seq += character
        elif seq:
            output.append(seq)
            seq = ""
    number = accumulator.append(None)
    if number is not None:
        output.append(number)
    elif seq:
        output.append(seq)
    return output


class SemanticText:
    __slots__ = ("value",)

    def __init__(self, value=""):
        self.value = value

    def __bool__(self):
        return bool(self.value)

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return self.value == other.value

    def __str__(self):
        return str(self.value)

    __repr__ = __str__

    def _is_lesser_than(self, other):
        for e1, e2 in itertools.zip_longest(
            separate_characters_and_numbers(self.value),
            separate_characters_and_numbers(other.value),
        ):
            if type(e1) is type(e2):
                if e1 == e2:
                    continue
                else:
                    return e1 < e2
            elif e1 is None:
                return True
            elif e2 is None:
                return False
            elif type(e1) is int:
                return True
            else:
                return False
        return False

    def __lt__(self, other):
        return self._is_lesser_than(other)


RE_DIGITS = re.compile(r"([0-9]+)")
RE_SUP_DIGITS = re.compile(f"([{CharClass.SUP_DIGITS}]+)")
RE_SUB_DIGITS = re.compile(f"([{CharClass.SUB_DIGITS}]+)")
RE_EMPTY = re.compile(r" {2,}")


def get_longest_number_in_string(text: str) -> int:
    return max(
        (
            len(m)
            for r in (RE_DIGITS, RE_SUP_DIGITS, RE_SUB_DIGITS)
            for m in r.findall(text)
        ),
        default=0,
    )


def pad_numbers_in_string(text: str, pad: int) -> str:
    text = RE_DIGITS.sub(lambda s: f" {s.group(1).rjust(pad, '0')} ", text)
    text = RE_SUP_DIGITS.sub(
        lambda s: f" {str(CharClass.parse_sup_digits(s.group(1))).rjust(pad, '0')} ",
        text,
    )
    text = RE_SUB_DIGITS.sub(
        lambda s: f" {str(CharClass.parse_sub_digits(s.group(1))).rjust(pad, '0')} ",
        text,
    )
    text = RE_EMPTY.sub(" ", text)
    return text
