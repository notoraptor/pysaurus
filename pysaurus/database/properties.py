from typing import Union

from pysaurus.application import exceptions
from pysaurus.core.enumeration import Enumeration

DefType = Union[bool, int, float, str, list, tuple]


class PropType:
    __slots__ = ("name", "type", "enumeration", "default", "multiple")

    def __init__(self, name: str, definition: DefType, multiple: bool = False):
        name = name.strip()
        if not name:
            raise exceptions.MissingPropertyName()
        if isinstance(definition, (bool, int, float, str)):
            prop_type = type(definition)
            enumeration = set()
            default = definition
            if prop_type is str:
                default = default.strip()
        elif isinstance(definition, (list, tuple)):
            enum_type = Enumeration(definition)
            prop_type = enum_type.type
            enumeration = enum_type.values
            default = definition[0]
        else:
            raise exceptions.InvalidPropertyDefinition(definition)
        self.name = name
        self.type = prop_type
        self.enumeration = enumeration
        self.default = default
        self.multiple = multiple

    @property
    def key(self):
        return (
            self.name,
            self.type,
            self.default,
            self.multiple,
            tuple(sorted(self.enumeration)),
        )

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return self.key == other.key

    def __call__(self, value=None):
        return self.new() if value is None else self.validate(value)

    def new(self):
        return [] if self.multiple else self.default

    def validate(self, value):
        if self.multiple:
            if not isinstance(value, (list, tuple, set)):
                raise exceptions.InvalidMultiplePropertyValue(self, value)
            if not isinstance(value, set):
                value = set(value)
            for element in value:
                if not isinstance(element, self.type):
                    raise exceptions.InvalidPropertyValue(self, element)
            if self.enumeration:
                for element in value:
                    if element not in self.enumeration:
                        raise exceptions.InvalidPropertyValue(self, element)
            return sorted(value)

        if self.type is float and isinstance(value, int):
            value = float(value)
        if not isinstance(value, self.type):
            raise exceptions.InvalidPropertyValue(self, value)
        if self.enumeration and value not in self.enumeration:
            raise exceptions.InvalidPropertyValue(self, value)
        return value

    def to_json(self):
        return {
            "name": self.name,
            "type": self.type.__name__,
            "enumeration": list(self.enumeration) if self.enumeration else None,
            "defaultValue": self.new(),
            "multiple": self.multiple,
        }

    def to_dict(self):
        if self.enumeration:
            definition = [self.default] + list(self.enumeration - {self.default})
        else:
            definition = self.default
        return {"n": self.name, "d": definition, "m": self.multiple}

    @classmethod
    def from_dict(cls, dct):
        return cls(dct["n"], dct["d"], dct["m"])
