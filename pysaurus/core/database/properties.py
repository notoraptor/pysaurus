from typing import Union
from pysaurus.core.classes import Enumeration

DefType = Union[bool, int, float, str, list, tuple]


class PropType:

    __slots__ = ('name', 'type', 'default', 'multiple')

    def __init__(self, name: str, definition: DefType, multiple: bool = False):
        self.name = name.strip()
        if not self.name:
            raise ValueError('Name needed for a property')
        if isinstance(definition, (bool, int, float, str)):
            self.type = type(definition)
            self.default = definition
        elif isinstance(definition, (list, tuple)):
            self.type = Enumeration(definition)
            self.default = definition[0]
        else:
            raise ValueError('Invalid prop type definition: should be either a bool, int, float, str, '
                             'or list|tuple of values from a same type to define an enumeration '
                             '(first value will be default value).')
        self.multiple = multiple

    def __call__(self, value=None):
        if value is None:
            return self.new()
        return self.validate(value)

    def new(self):
        return [] if self.multiple else self.type(self.default)

    def validate(self, value):
        if self.multiple:
            if not isinstance(value, (list, tuple, set)):
                raise ValueError('Expected a list, tuple or set of values for a multiple prop.')
            return list({self.type(element) for element in value})
        return self.type(value)

    def to_dict(self):
        if isinstance(self.type, Enumeration):
            definition = [self.default] + [element for element in self.type.values if element != self.default]
        else:
            definition = self.default
        return {
            'n': self.name,
            'd': definition,
            'm': self.multiple
        }

    def to_json(self):
        prop_name = self.name
        if isinstance(self.type, Enumeration):
            prop_type = 'enum'
            prop_values = sorted(self.type.values)
        else:
            prop_type = self.type.__name__
            prop_values = None
        prop_default = [] if self.multiple else self.default
        prop_multiple = self.multiple
        return {
            'name': prop_name,
            'type': prop_type,
            'values': prop_values,
            'defaultValue': prop_default,
            'multiple': prop_multiple
        }


    @classmethod
    def from_dict(cls, dct):
        return cls(dct['n'], dct['d'], dct['m'])
