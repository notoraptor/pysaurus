from typing import Collection, Sequence, cast

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

# Types whose domain is open, i.e. too large to spell out. Only for those does
# it carry information to declare an explicit enumeration, or to allow several
# values per video. `bool` is excluded on purpose: its domain is already exactly
# {False, True}, so an enumeration would merely restate the type, and a
# multi-valued bool could only ever hold that same full domain.
OPEN_DOMAIN_PROP_TYPES = frozenset({"str", "int", "float"})


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
        if type == "bool":
            # Enforced here rather than in define() so that a PropType rebuilt
            # from the database is held to the same invariant. Existing
            # databases are brought in line by migration m0005.
            if multiple:
                raise exceptions.BooleanPropertyCannotBeMultiple(name)
            if enumeration:
                raise exceptions.BooleanPropertyCannotBeEnumerated(name, enumeration)
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

    @property
    def possible_values(self) -> list[PropUnitType] | None:
        """The values this property accepts, or None when unconstrained.

        A bool is its own two-value domain: it is implied by the type and
        deliberately never stored (see OPEN_DOMAIN_PROP_TYPES), so it is
        derived here instead of being read from `enumeration`.

        This answers *which values are permitted*, not which widget to build:
        a bool is edited with dedicated radio buttons rather than a list of
        its two values, so frontends still branch on `type` to choose a
        widget. Ask this one whenever the values themselves are needed --
        to fill a choice, or to display the domain (see
        interface.common.prop_format).
        """
        if self.type == "bool":
            return [False, True]
        return self.enumeration

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
            return self.validate_on_multiple_prop_type(value)
        else:
            return self.validate_on_unique_prop_type(value)

    def validate_on_multiple_prop_type(self, value: PropRawType) -> list[PropUnitType]:
        if not isinstance(value, (list, tuple, set)):
            raise exceptions.InvalidMultiplePropertyValue(self, value)
        # Type-check the values as given, before deduplicating: True == 1 and
        # hashes alike, so set([1, True]) is {1} and set([True, 1]) is {True}.
        # Checking the set would therefore accept or reject a stray bool on an
        # int property depending on the order the values came in.
        for element in cast(Collection[PropUnitType], value):
            # Exact type, not isinstance: bool is a subclass of int, so
            # isinstance would silently let True through on an int property.
            if type(element) is not self.python_type:
                raise exceptions.InvalidPropertyValue(self, element)
        elements = set(cast(Collection[PropUnitType], value))
        if self._enum_set:
            for element in elements:
                if element not in self._enum_set:
                    raise exceptions.InvalidPropertyValue(self, element)
        return sorted(elements)

    def validate_on_unique_prop_type(self, value: PropRawType) -> PropUnitType:
        # Exact type, not isinstance: bool is a subclass of int, so isinstance
        # would promote True to 1.0 here, and let it through as an int below.
        if self.python_type is float and type(value) is int:
            value = float(value)
        if type(value) is not self.python_type:
            raise exceptions.InvalidPropertyValue(self, value)
        if self._enum_set and value not in self._enum_set:
            raise exceptions.InvalidPropertyValue(self, value)
        assert isinstance(value, PropUnitType)
        return value

    def instantiate(self, values: Collection[PropUnitType]) -> list[PropUnitType]:
        if not values:
            return []
        if self.multiple:
            return self.validate_on_multiple_prop_type(values)
        else:
            (value,) = values
            return [self.validate_on_unique_prop_type(value)]

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
            enumeration = list(cast(Collection[PropUnitType], definition))
            default_value = [enumeration[0]]
        else:
            if not isinstance(definition, (str, bool, int, float)):
                raise InvalidPropertyDefinition(definition)
            default_value = [definition]

        if prop_type is float:
            # Same tolerance as validate_on_unique_prop_type: ints are accepted
            # for convenience and promoted. Exact types, so a bool -- a subclass
            # of int, yet an answer rather than a quantity -- is refused instead
            # of being promoted to 1.0, and reading a float out of text is the
            # caller's job.
            if any(
                type(element) not in (int, float)
                for element in (*enumeration, *default_value)
            ):
                raise InvalidPropertyDefinition(definition)
            enumeration = [float(element) for element in enumeration]
            default_value = [float(element) for element in default_value]
        elif prop_type is int:
            # Exact type, as validate() demands of every value afterwards: an
            # isinstance check would let a bool through, and a float or a str
            # would be stored as a default no int value can ever equal.
            if any(
                type(element) is not int for element in (*enumeration, *default_value)
            ):
                raise InvalidPropertyDefinition(definition)
        elif prop_type is str:
            enumeration = [str(element).strip() for element in enumeration]
            default_value = [str(element).strip() for element in default_value]
        elif prop_type is bool and any(
            type(element) is not bool for element in default_value
        ):
            # No coercion here: bool("false") is True, so reading a bool out of
            # text is the caller's job. Values must already be real bools, as
            # validate_on_unique_prop_type demands of every value afterwards.
            raise InvalidPropertyDefinition(definition)

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
