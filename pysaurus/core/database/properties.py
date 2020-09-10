from typing import Union

from pysaurus.core.classes import Enumeration

DefType = Union[bool, int, float, str, list, tuple]


class PropType:
    __slots__ = ('name', 'type', 'enumeration', 'default', 'multiple')

    def __init__(self, name: str, definition: DefType, multiple: bool = False):
        name = name.strip()
        if not name:
            raise ValueError('Name needed for a property.')
        if isinstance(definition, (bool, int, float, str)):
            prop_type = type(definition)
            default = definition
            enumeration = None
            if prop_type is str:
                default = default.strip()
        elif isinstance(definition, (list, tuple)):
            enum_type = Enumeration(definition)
            prop_type = enum_type.type
            default = definition[0]
            enumeration = enum_type.values
        else:
            raise ValueError('Invalid prop type definition: should be either a bool, int, float, str, '
                             'or list|tuple of values from a same type to define an enumeration '
                             '(first value will be default value).')
        self.name = name
        self.type = prop_type
        self.enumeration = enumeration
        self.default = default
        self.multiple = multiple

    def __call__(self, value=None):
        return self.new() if value is None else self.validate(value)

    def new(self):
        return [] if self.multiple else self.default

    def validate(self, value):
        if self.multiple:
            if not isinstance(value, (list, tuple, set)):
                raise ValueError(
                    'Property %s: expected a list, tuple or set of values for a multiple prop.' % self.name)
            if not isinstance(value, set):
                value = set(value)
            for element in value:
                if not isinstance(element, self.type):
                    raise ValueError('Property %s: expected type %s, got %s' % (self.name, self.type, type(element)))
            if self.enumeration:
                for element in value:
                    if element not in self.enumeration:
                        raise ValueError('Property %s: forbidden values (%s), allowed: %s' % (
                            self.name, element, ', '.join(str(el) for el in self.enumeration)))
            return sorted(value)

        if self.type is float and isinstance(value, int):
            value = float(value)
        if not isinstance(value, self.type):
            raise ValueError('Property %s: expected type %s, got %s' % (self.name, self.type, type(value)))
        if self.enumeration and value not in self.enumeration:
            raise ValueError('Property %s: forbidden values (%s), allowed: %s' % (
                self.name, value, ', '.join(str(el) for el in self.enumeration)))
        return value

    def to_dict(self):
        if self.enumeration:
            definition = [self.default] + list(self.enumeration - {self.default})
        else:
            definition = self.default
        return {'n': self.name,
                'd': definition,
                'm': self.multiple}

    def to_json(self):
        return {
            'name': self.name,
            'type': self.type.__name__,
            'enumeration': list(self.enumeration) if self.enumeration else None,
            'defaultValue': [] if self.multiple else self.default,
            'multiple': self.multiple
        }

    @classmethod
    def from_dict(cls, dct):
        return cls(dct['n'], dct['d'], dct['m'])
