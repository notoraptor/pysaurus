from pysaurus.application import exceptions
from pysaurus.core.json_type import Type
from pysaurus.core.schematizable import Schema, WithSchema, schema_prop
from pysaurus.properties.properties import PropValueType


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
