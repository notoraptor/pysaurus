from pysaurus.core.functions import separate_text_and_numbers


class IncomparableError(ValueError):
    pass


def _semantic_comparable(v):
    return v.lower() if isinstance(v, str) else v


class SemanticText:
    __slots__ = ("value", "comparable")

    def __init__(self, value=""):
        self.value = value
        self.comparable = separate_text_and_numbers(value)

    def __bool__(self):
        return bool(self.comparable)

    def __hash__(self):
        return hash(self.comparable)

    def __str__(self):
        return str(self.comparable)

    def raise_incomparable(self, other):
        raise IncomparableError(self.comparable, other.comparable)

    def __lt__(self, other):
        try:
            if len(self.comparable) != len(other.comparable):
                self.raise_incomparable(other)
            # semantic
            for a, b in zip(self.comparable, other.comparable):
                a = _semantic_comparable(a)
                b = _semantic_comparable(b)
                if type(a) != type(b):
                    self.raise_incomparable(other)
                if a != b:
                    return a < b
            # raw
            for a, b in zip(self.comparable, other.comparable):
                if type(a) != type(b):
                    self.raise_incomparable(other)
                if a != b:
                    return a < b
            return False
        except IncomparableError:
            if self.value.lower() < other.value.lower():
                return True
            else:
                return self.value < other.value
