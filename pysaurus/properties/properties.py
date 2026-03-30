from typing import Collection, Sequence

from pysaurus.application import exceptions
from pysaurus.application.exceptions import InvalidPropertyDefinition
from pysaurus.core.enumeration import Enumeration

PropUnitType = bool | int | float | str
PropRawType = PropUnitType | Collection[PropUnitType]
PropValueType = PropUnitType | list[PropUnitType]


def _str_to_bool(value: str) -> bool:
    return bool(int(value))


PROP_UNIT_TYPES = {bool, int, float, str}
PROP_UNIT_TYPE_MAP = {t.__name__: t for t in PROP_UNIT_TYPES}
PROP_UNIT_CONVERTER = {**PROP_UNIT_TYPE_MAP, "bool": _str_to_bool}


class PropType:
    __slots__ = (
        "name",
        "type",
        "multiple",
        "default",
        "enumeration",
        "property_id",
        "_enum_set",
    )

    def __init__(
        self,
        name: str,
        type: str,
        multiple: bool,
        default: list[PropUnitType],
        enumeration: list[PropUnitType] | None,
        property_id: int | None = None,
    ):
        self.name = name
        self.type = type
        self.multiple = multiple
        self.default = default
        self.enumeration = enumeration
        self.property_id = property_id
        self._enum_set = set(enumeration or ())

    @property
    def python_type(self) -> type:
        return PROP_UNIT_TYPE_MAP[self.type]

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "multiple": self.multiple,
            "defaultValues": self.default,
            "enumeration": self.enumeration,
            "property_id": self.property_id,
        }

    # =========================================================================
    # SQL conversion
    # =========================================================================

    def to_str(self, values: list) -> list[str]:
        if self.type == "str":
            return values
        elif self.type == "bool":
            return [str(int(value)) for value in values]
        else:
            return [str(value) for value in values]

    def from_string(self, value: str) -> PropUnitType:
        if self.type == "str":
            return value
        elif self.type == "bool":
            return bool(int(value))
        else:
            return self.python_type(value)

    def from_strings(self, values: Collection[str]) -> Collection[PropUnitType]:
        if not values:
            return []
        if not self.multiple and len(values) != 1:
            raise exceptions.InvalidUniquePropertyValue(self, values)
        return [self.from_string(v) for v in values]

    # =========================================================================
    # Validation
    # =========================================================================

    def validate(self, value: PropRawType) -> PropValueType:
        if self.multiple:
            return self._validate_on_multiple_prop_type(value)
        else:
            return self._validate_on_unique_prop_type(value)

    def _validate_on_multiple_prop_type(self, value: PropRawType) -> list[PropUnitType]:
        if not isinstance(value, (list, tuple, set)):
            raise exceptions.InvalidMultiplePropertyValue(self, value)
        if not isinstance(value, set):
            value = set(value)
        for element in value:
            if not isinstance(element, self.python_type):
                raise exceptions.InvalidPropertyValue(self, element)
        if self._enum_set:
            for element in value:
                if element not in self._enum_set:
                    raise exceptions.InvalidPropertyValue(self, element)
        return sorted(value)

    def _validate_on_unique_prop_type(self, value: PropRawType) -> PropUnitType:
        if self.python_type is float and isinstance(value, int):
            value = float(value)
        if not isinstance(value, self.python_type):
            raise exceptions.InvalidPropertyValue(self, value)
        if self._enum_set and value not in self._enum_set:
            raise exceptions.InvalidPropertyValue(self, value)
        assert isinstance(value, PropUnitType)
        return value

    def instantiate(self, values: Collection[PropUnitType]) -> list[PropUnitType]:
        if not values:
            return []
        if self.multiple:
            return self._validate_on_multiple_prop_type(values)
        else:
            (value,) = values
            return [self._validate_on_unique_prop_type(value)]

    # =========================================================================
    # Factory
    # =========================================================================

    def __str__(self):
        return (
            f"PropType"
            f"({self.name}, "
            f"{self.type}, "
            f"multiple={self.multiple}, "
            f"default={repr(self.default)}, "
            f"enumeration={repr(self.enumeration)})"
        )

    __repr__ = __str__

    @classmethod
    def define(
        cls, name: str, prop_type: str | type, definition: PropRawType, multiple: bool
    ) -> "PropType":
        name = name.strip()
        if not name:
            raise exceptions.MissingPropertyName()

        if isinstance(prop_type, str):
            prop_type = PROP_UNIT_TYPE_MAP[prop_type]
        assert prop_type in PROP_UNIT_TYPES

        enumeration: Sequence[PropUnitType] = []
        default_value: list[PropUnitType]
        if isinstance(definition, (list, tuple)):
            enumeration = list(definition)
            default_value = [enumeration[0]]
        else:
            if not isinstance(definition, (str, bool, int, float)):
                raise InvalidPropertyDefinition(definition)
            default_value = [definition]

        if prop_type is float:
            enumeration = [float(element) for element in enumeration]
            default_value = [float(element) for element in default_value]
        elif prop_type is str:
            enumeration = [element.strip() for element in enumeration]
            default_value = [str(element).strip() for element in default_value]

        if enumeration:
            enum_type = Enumeration(enumeration)
            enumeration = [enumeration[0]] + sorted(enum_type.values - {enumeration[0]})

        return cls(
            name=name,
            type=prop_type.__name__,
            multiple=multiple,
            default=[] if multiple else default_value,
            enumeration=list(enumeration) if enumeration else None,
        )
