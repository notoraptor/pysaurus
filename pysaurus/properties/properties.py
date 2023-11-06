from typing import Union

from pysaurus.application import exceptions
from pysaurus.core.enumeration import Enumeration
from pysaurus.core.json_type import Type
from pysaurus.core.schematizable import Schema, WithSchema, schema_prop

DefType = Union[bool, int, float, str, list, tuple]
PropValueType = Union[bool, int, float, str, list]

PROP_UNIT_TYPES = {bool, int, float, str}
PROP_UNIT_TYPE_MAP = {t.__name__: t for t in PROP_UNIT_TYPES}


class PropType(WithSchema):
    __slots__ = ()
    SCHEMA = Schema(
        (
            Type("name", (str, "n")),
            Type("definition", (object, "d")),
            Type("multiple", "m", False),
        )
    )

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
        super().__init__({"n": name, "d": definition, "m": multiple})

    name = schema_prop("name")
    definition = schema_prop("definition")
    multiple = schema_prop("multiple")

    default = property(
        lambda self: self.definition[0] if self.is_enum() else self.definition
    )
    type = property(lambda self: type(self.default))
    enumeration = property(lambda self: self.definition if self.is_enum() else None)

    def __call__(self, value=None) -> PropValueType:
        return self.new() if value is None else self.validate(value)

    def is_enum(self, with_values=None):
        return isinstance(self.definition, list) and (
            with_values is None or set(self.definition) == set(with_values)
        )

    def new(self) -> PropValueType:
        return [] if self.multiple else self.default

    def validate(self, value) -> PropValueType:
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

    def describe(self) -> dict:
        return {
            "name": self.name,
            "type": self.type.__name__,
            "enumeration": self.enumeration,
            "defaultValue": self.new(),
            "multiple": self.multiple,
        }

    @classmethod
    def from_dict(cls, dct: dict, **kwargs):
        return cls(**cls.SCHEMA.to_long_keys(dct))


class PropTypeValidator:
    __slots__ = ("name", "type", "enumeration", "multiple")

    def __init__(self, prop_desc: dict):
        self.name = prop_desc["name"]
        self.type = PROP_UNIT_TYPE_MAP[prop_desc["type"]]
        self.enumeration = prop_desc["enumeration"]
        self.multiple = prop_desc["multiple"]

    def validate(self, value: PropValueType) -> PropValueType:
        if self.multiple:
            if not isinstance(value, (list, tuple, set)):
                raise exceptions.InvalidMultiplePropertyValue(self, value)
            if not isinstance(value, set):
                value = set(value)
            for element in value:
                if not isinstance(element, self.type):
                    raise exceptions.InvalidPropertyValue(self, element)
            if self.enumeration:
                enumeration = set(self.enumeration)
                for element in value:
                    if element not in enumeration:
                        raise exceptions.InvalidPropertyValue(self, element)
            return sorted(value)

        if self.type is float and isinstance(value, int):
            value = float(value)
        if not isinstance(value, self.type):
            raise exceptions.InvalidPropertyValue(self, value)
        if self.enumeration and value not in set(self.enumeration):
            raise exceptions.InvalidPropertyValue(self, value)
        return value
