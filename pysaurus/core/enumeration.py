from typing import Iterable


class EnumerationError(Exception):
    pass


class EnumerationTypeError(EnumerationError):
    pass


class EnumerationValueError(EnumerationError):
    pass


class Enumeration:
    __slots__ = "values", "type"

    def __init__(self, enum_values: Iterable):
        self.values = set(enum_values)
        if len(self.values) < 2:
            raise EnumerationError(self.values)
        types = {type(value) for value in self.values}
        if len(types) != 1:
            raise EnumerationTypeError(types)
        self.type = next(iter(types))
        if self.type not in (bool, int, float, str):
            raise EnumerationTypeError(self.type)

    def __call__(self, value):
        if value not in self.values:
            raise EnumerationValueError(self, value)
        return value

    def __str__(self):
        return "{" + (", ".join(sorted(self.values))) + "}"

    __repr__ = __str__
