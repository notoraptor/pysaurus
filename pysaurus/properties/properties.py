from typing import Collection

from pysaurus.application import exceptions
from pysaurus.core.enumeration import Enumeration

PropUnitType = bool | int | float | str
PropRawType = PropUnitType | Collection
PropValueType = PropUnitType | list


def _str_to_bool(value: str) -> bool:
    return bool(int(value))


PROP_UNIT_TYPES = {bool, int, float, str}
PROP_UNIT_TYPE_MAP = {t.__name__: t for t in PROP_UNIT_TYPES}
PROP_UNIT_CONVERTER = {**PROP_UNIT_TYPE_MAP, "bool": _str_to_bool}


class PropTypeDesc:
    __slots__ = ("_desc",)

    def __init__(self, prop_desc: dict):
        self._desc = prop_desc

    @property
    def name(self) -> str:
        return self._desc["name"]

    @property
    def type(self):
        return PROP_UNIT_TYPE_MAP[self._desc["type"]]

    @property
    def enumeration(self) -> list[PropUnitType] | None:
        return self._desc["enumeration"]

    @property
    def multiple(self) -> bool:
        return self._desc["multiple"]

    @property
    def default(self) -> list[PropUnitType]:
        return self._desc["defaultValues"]

    @property
    def property_id(self) -> int | None:
        return self._desc.get("property_id")


class PropTypeValidator(PropTypeDesc):
    __slots__ = ("to_str", "_enum_set")

    def __init__(self, prop_desc: dict):
        super().__init__(prop_desc)
        if self.type is str:
            to_str = self._str_to_sql
        elif self.type is bool:
            to_str = self._bool_to_sql
        else:
            to_str = self._value_to_sql

        self.to_str = to_str
        self._enum_set = set(self.enumeration or ())

    def _bool_to_sql(self, values: list[bool]) -> list[str]:
        return [str(int(value)) for value in values]

    def _str_to_sql(self, values: list[str]) -> list[str]:
        return values

    def _value_to_sql(self, values: list) -> list[str]:
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
            if self._enum_set:
                for element in value:
                    if element not in self._enum_set:
                        raise exceptions.InvalidPropertyValue(self, element)
            return sorted(value)

        if self.type is float and isinstance(value, int):
            value = float(value)
        if not isinstance(value, self.type):
            raise exceptions.InvalidPropertyValue(self, value)
        if self._enum_set and value not in self._enum_set:
            raise exceptions.InvalidPropertyValue(self, value)
        return value

    def instantiate(self, values: Collection[PropUnitType]) -> list[PropUnitType]:
        if not values:
            return []
        if self.multiple:
            return self.validate(values)
        else:  # list must contain only 1 value.
            (value,) = values
            return [self.validate(value)]

    def from_strings(self, values: Collection[str]) -> Collection[PropUnitType]:
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

    @classmethod
    def define(
        cls,
        name: str,
        prop_type: str | type,
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
