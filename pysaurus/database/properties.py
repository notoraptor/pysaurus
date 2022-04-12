from typing import Union

from pysaurus.application import exceptions
from pysaurus.core.enumeration import Enumeration
from pysaurus.core.jsonable import Jsonable

DefType = Union[bool, int, float, str, list, tuple]


class PropType(Jsonable):
    name: str
    definition: object
    multiple = False
    __short__ = {"name": "n", "definition": "d", "multiple": "m"}

    def __init__(self, name: str, definition: DefType, multiple: bool = False):
        name = name.strip()
        if not name:
            raise exceptions.MissingPropertyName()
        if not isinstance(definition, (bool, int, float, str, list, tuple)):
            raise exceptions.InvalidPropertyDefinition(definition)
        if isinstance(definition, str):
            definition = definition.strip()
        elif isinstance(definition, (list, tuple)):
            enum_type = Enumeration(definition)
            definition = [definition[0]] + sorted(enum_type.values - {definition[0]})
        super().__init__(name=name, definition=definition, multiple=multiple)

    default = property(
        lambda self: self.definition[0] if self.is_enum() else self.definition
    )
    type = property(lambda self: type(self.default))

    def __call__(self, value=None):
        return self.new() if value is None else self.validate(value)

    def is_enum(self):
        return isinstance(self.definition, list)

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
            if self.is_enum():
                enumeration = set(self.definition)
                for element in value:
                    if element not in enumeration:
                        raise exceptions.InvalidPropertyValue(self, element)
            return sorted(value)

        if self.type is float and isinstance(value, int):
            value = float(value)
        if not isinstance(value, self.type):
            raise exceptions.InvalidPropertyValue(self, value)
        if self.is_enum() and value not in set(self.definition):
            raise exceptions.InvalidPropertyValue(self, value)
        return value

    def describe(self):
        return {
            "name": self.name,
            "type": self.type.__name__,
            "enumeration": self.definition if self.is_enum() else None,
            "defaultValue": self.new(),
            "multiple": self.multiple,
        }
