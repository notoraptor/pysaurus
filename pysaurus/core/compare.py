class NegativeComparator:
    """Helper class for reverse comparison"""

    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return self.value == other.value

    def __lt__(self, other):
        return other.value < self.value


def to_comparable(value, reverse=False):
    return NegativeComparator(value) if reverse else value
