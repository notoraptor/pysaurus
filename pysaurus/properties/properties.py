from typing import Collection, Sequence, Union, List

from pysaurus.application import exceptions
from pysaurus.core.enumeration import Enumeration
from pysaurus.core.json_type import Type
from pysaurus.core.schematizable import Schema, WithSchema, schema_prop
from pysaurus.core import functions

PropUnitType = Union[bool, int, float, str]
PropRawType = Union[bool, int, float, str, Collection]
PropValueType = Union[bool, int, float, str, list]

PROP_UNIT_TYPES = {bool, int, float, str}
PROP_UNIT_TYPE_MAP = {t.__name__: t for t in PROP_UNIT_TYPES}

PROP_UNIT_CONVERTER = PROP_UNIT_TYPE_MAP.copy()
PROP_UNIT_CONVERTER["bool"] = lambda value: bool(int(value))


class PropType(WithSchema):
    __slots__ = ()
    SCHEMA = Schema(
        (
            Type("name", (str, "n")),
            Type("definition", (object, "d")),
            Type("multiple", "m", False),
        )
    )

    name = schema_prop("name")
    definition = schema_prop("definition")
    multiple = schema_prop("multiple")

    default = property(
        lambda self: self.definition[0] if self.is_enum() else self.definition
    )
    type = property(lambda self: type(self.default))
    enumeration = property(
        lambda self: sorted(self.definition) if self.is_enum() else None
    )

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
            "defaultValues": [] if self.multiple else [self.default],
            "multiple": self.multiple,
        }


class PropTypeValidator:
    __slots__ = (
        "name",
        "type",
        "enumeration",
        "multiple",
        "default",
        "property_id",
        "as_sql",
    )

    def __init__(self, prop_desc: dict):
        self.name = prop_desc["name"]
        self.type = PROP_UNIT_TYPE_MAP[prop_desc["type"]]
        self.enumeration = prop_desc["enumeration"]
        self.multiple = prop_desc["multiple"]
        self.default = prop_desc["defaultValues"]
        self.property_id = prop_desc.get("property_id")

        if self.type is str:
            sqler = self._str_to_sql
        elif self.type is bool:
            sqler = self._bool_to_sql
        else:
            sqler = self._value_to_sql

        self.as_sql = sqler

    def _bool_to_sql(self, values: list) -> List[str]:
        return [str(int(value)) for value in values]

    def _str_to_sql(self, values: list) -> List[str]:
        return values

    def _value_to_sql(self, values: list) -> List[str]:
        return [str(value) for value in values]

    def __str__(self):
        return (
            f"{type(self).__name__}"
            f"({self.name}, "
            f"{self.type.__name__}, "
            f"multiple={self.multiple}, "
            f"default={repr(self.default)}, "
            f"enumeration={repr(self.enumeration)})"
        )

    __repr__ = __str__

    def validate(self, value: PropRawType) -> PropValueType:
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

    def instantiate(self, values: Collection[PropUnitType]) -> Collection[PropUnitType]:
        if not values:
            return []
        if self.multiple:
            return self.validate(values)
        else:  # list must contain only 1 value.
            (value,) = values
            return [self.validate(value)]

    def from_strings(self, values: Collection[str]) -> Sequence[PropUnitType]:
        if not values:
            return []
        if not self.multiple and len(values) != 1:
            raise exceptions.InvalidUniquePropertyValue(self, values)
        if self.type is str:
            return values
        elif self.type is bool:
            return [bool(int(value)) for value in values]
        else:
            return [self.type(value) for value in values]

    def from_string(self, value: str) -> PropUnitType:
        return (
            value
            if self.type is str
            else (bool(int(value)) if self.type is bool else self.type(value))
        )

    def plain_from_strings(self, values: Sequence[str]) -> PropValueType:
        values = self.from_strings(values)
        return values if self.multiple else values[0]

    @classmethod
    def define(
        cls,
        name: str,
        prop_type: Union[str, type],
        definition: PropRawType,
        multiple: bool,
        *,
        describe=False,
    ) -> dict:
        name = name.strip()
        if not name:
            raise exceptions.MissingPropertyName()

        if isinstance(prop_type, str):
            prop_type = PROP_UNIT_TYPE_MAP[prop_type]
        assert prop_type in PROP_UNIT_TYPES
        if prop_type is float:
            if isinstance(definition, (list, tuple)):
                definition = [float(element) for element in definition]
            else:
                definition = float(definition)
        elif prop_type is str:
            if isinstance(definition, (list, tuple)):
                definition = [element.strip() for element in definition]
            else:
                definition = definition.strip()

        if not isinstance(definition, (bool, int, float, str, list, tuple)):
            raise exceptions.InvalidPropertyDefinition(definition)
        if isinstance(definition, (list, tuple)):
            enum_type = Enumeration(definition)
            definition = [definition[0]] + sorted(enum_type.values - {definition[0]})

        if describe:
            enumeration = definition if isinstance(definition, list) else None
            return {
                "name": name,
                "type": prop_type.__name__,
                "multiple": multiple,
                "default": enumeration[0] if enumeration else definition,
                "enumeration": enumeration,
            }
        else:
            return {"name": name, "definition": definition, "multiple": multiple}
