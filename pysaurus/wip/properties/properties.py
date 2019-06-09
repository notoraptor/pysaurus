import re

from pysaurus.core.utils.functions import is_iterable, ensure_set, to_printable
from pysaurus.wip.properties import property_errors


class PropertyType:
    __slots__ = ('__name', '__type', '__enumeration', '__default', '__multiple')
    TYPES = (bool, int, float, str)
    DEFAULT = {bool: False, int: 0, float: 0.0, str: ''}
    STR_TO_TYPE = {'b': bool, 'i': int, 'f': float, 's': str}
    TYPE_TO_STR = {_type: _str for (_str, _type) in STR_TO_TYPE.items()}

    def __init__(self, name, property_type, enumeration=None, default=None, multiple=None):
        name = PropertyType.__assert_name(name)
        multiple = bool(multiple)
        property_type = PropertyType.__assert_type(property_type)
        enumeration = PropertyType.__assert_enumeration(enumeration, property_type)
        default = PropertyType.__assert_default(default, multiple, property_type, enumeration)
        # string
        self.__name = name
        # bool
        self.__multiple = multiple
        # type
        self.__type = property_type
        # None or set
        self.__enumeration = enumeration
        # None, variable (for unique property) or set (for multiple property)
        self.__default = default

    def __str__(self):
        wrappers = ('[', ']') if self.__multiple else ('(', ')')
        pieces = [self.__name, wrappers[0], self.__type.__name__]
        if self.__enumeration:
            pieces.append(' in {%s}' % ', '.join(str(to_printable(val)) for val in sorted(self.__enumeration)))
        pieces.append(wrappers[1])
        if self.__default is not None:
            pieces.append(' = ')
            if self.__multiple:
                pieces.append('{%s}' % ', '.join(str(to_printable(val)) for val in sorted(self.__default)))
            else:
                pieces.append(str(to_printable(self.__default)))
        return '<%s>' % ''.join(pieces)

    def __hash__(self):
        return hash(self.comparable)

    def __eq__(self, other):
        return self.comparable == other.comparable

    def __lt__(self, other):
        return self.comparable < other.comparable

    @property
    def comparable(self):
        comparable_enumeration = [] if self.__enumeration is None else sorted(self.__enumeration)
        comparable_default = sorted(self.default) if self.__multiple else [self.default]
        return (self.__name, self.__type.__name__, self.__multiple,
                tuple(comparable_enumeration), tuple(comparable_default))

    @property
    def name(self):
        return self.__name

    @property
    def multiple(self):
        return self.__multiple

    @property
    def type(self):
        return self.__type

    @property
    def enumeration(self):
        return set(self.__enumeration)

    @property
    def default(self):
        if self.__default is None:
            return {PropertyType.DEFAULT[self.__type]} if self.__multiple else PropertyType.DEFAULT[self.__type]
        return set(self.__default) if self.__multiple else self.__default

    @name.setter
    def name(self, new_name):
        self.__name = PropertyType.__assert_name(new_name)

    @multiple.setter
    def multiple(self, new_multiple):
        new_multiple = bool(new_multiple)
        if self.__multiple != new_multiple:
            if self.__default is not None:
                if new_multiple:
                    self.__default = {self.__default}
                else:
                    if len(self.__default) != 1:
                        raise ValueError(
                            'Cannot convert a property from multiple to unique with multiple default values. '
                            'Please set default value to a singleton before.')
                    self.__default = next(iter(self.__default))
            self.__multiple = new_multiple

    @type.setter
    def type(self, new_type):
        new_type = PropertyType.__assert_type(new_type)
        if self.__type != new_type:
            if self.__enumeration is not None:
                self.__enumeration = {new_type(value) for value in self.__enumeration}
            if self.__default is not None:
                self.__default = {new_type(v) for v in self.__default} if self.__multiple else new_type(self.__default)
            self.__type = new_type

    @enumeration.setter
    def enumeration(self, new_enumeration):
        new_enumeration = PropertyType.__assert_enumeration(new_enumeration, self.__type)
        if new_enumeration and self.__default is not None:
            for value in (self.__default if self.multiple else [self.__default]):
                if value not in new_enumeration:
                    raise property_errors.PropertyAllowedError(new_enumeration, value)
        self.__enumeration = new_enumeration

    @default.setter
    def default(self, new_default):
        self.__default = PropertyType.__assert_default(new_default, self.__multiple, self.__type, self.__enumeration)

    def new(self, new_value):
        if new_value is not None and self.__multiple:
            if not is_iterable(new_value):
                raise property_errors.PropertyIterableError(new_value)
            new_value = ensure_set(new_value)
            if not new_value:
                new_value = None
        if new_value is None:
            new_value = self.default
        else:
            PropertyType.__assert_value_is_valid(new_value, self.__type, self.__enumeration, self.__multiple)
        return PropertyValue(self, new_value)

    def add(self, previous_value, new_value):
        # type: (PropertyValue, object) -> PropertyValue
        if not self.__multiple:
            raise ValueError('Cannot extend value for a unique property.')
        if not previous_value.type_is(self):
            raise ValueError('Value does not belong to this property.')
        if not is_iterable(new_value):
            raise property_errors.PropertyIterableError(new_value)
        return self.new(previous_value.value | ensure_set(new_value))

    def remove(self, previous_value, new_value):
        # type: (PropertyValue, object) -> PropertyValue
        if not self.__multiple:
            raise ValueError('Cannot extend value for a unique property.')
        if not previous_value.type_is(self):
            raise ValueError('Value does not belong to this property.')
        if not is_iterable(new_value):
            raise property_errors.PropertyIterableError(new_value)
        return self.new(previous_value.value - ensure_set(new_value))

    def to_json(self):
        return {
            'n': self.__name,
            'm': self.__multiple,
            't': PropertyType.TYPE_TO_STR[self.__type],
            'e': self.__enumeration,
            'd': self.__default,
        }

    @staticmethod
    def from_json(dct):
        return PropertyType(
            name=dct['n'],
            multiple=dct['m'],
            property_type=PropertyType.STR_TO_TYPE[dct['t']],
            enumeration=dct['e'],
            default=dct['d']
        )

    @staticmethod
    def __assert_name(name):
        if not (isinstance(name, str) and re.match('^[A-Za-z0-9_]+$', name)):
            raise property_errors.PropertyNameError(name)
        return name

    @staticmethod
    def __assert_type(property_type):
        if property_type not in PropertyType.TYPES:
            raise property_errors.PropertyTypeError(property_type)
        return property_type

    @staticmethod
    def __assert_enumeration(enumeration, property_type):
        if enumeration is not None:
            if not is_iterable(enumeration):
                raise property_errors.PropertyIterableEnumError(enumeration)
            enumeration = ensure_set(enumeration)
            if not enumeration:
                return None
            for value in enumeration:
                if not isinstance(value, property_type):
                    raise property_errors.PropertyEnumTypeError(property_type, value)
        return enumeration

    @staticmethod
    def __assert_default(default, multiple, property_type, enumeration):
        if default is not None:
            if multiple:
                if not is_iterable(default):
                    raise property_errors.PropertyIterableDefaultError(default)
                default = ensure_set(default)
                if not default:
                    return None
            PropertyType.__assert_value_is_valid(default, property_type, enumeration, multiple)
        return default

    @staticmethod
    def __assert_value_is_valid(element, property_type, enumeration, multiple):
        if not multiple:
            element = [element]
        for value in element:
            if not isinstance(value, property_type):
                raise property_errors.PropertyValueTypeError(property_type, value)
            if enumeration and value not in enumeration:
                raise property_errors.PropertyAllowedError(enumeration, value)


class PropertyValue:
    __slots__ = ('__type', '__value')

    def __init__(self, property_type, raw):
        self.__type = property_type
        self.__value = raw

    @property
    def value(self):
        return set(self.__value) if self.__type.multiple else self.__value

    def type_is(self, property_type):
        return self.__type == property_type
