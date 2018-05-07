from pysaurus.utils import exceptions
from pysaurus.utils.common import is_sequence
from pysaurus.utils.json_compatible import JSONCompatible

_allowed_types = (bool, int, float, str)
_allowed_sequence_types = (list, set)
_type_name_to_type = {t.__name__: t for t in _allowed_types}
_sequence_type_name_to_type = {t.__name__: t for t in _allowed_sequence_types}


class PropertyType(JSONCompatible):
    __slots__ = {'__name', '__element_type', '__sequence_type', '__default'}

    def __init__(self, name, element_type, sequence_type=None, default=None):
        assert isinstance(name, str)
        assert element_type in _allowed_types
        assert sequence_type is None or sequence_type in _allowed_sequence_types
        self.__name = name
        self.__element_type = element_type
        self.__sequence_type = sequence_type
        self.__default = default
        if self.__default is not None:
            self.validate(self.__default)

    name = property(lambda self: self.__name)
    type = property(lambda self: self.__element_type)
    sequence_type = property(lambda self: self.__sequence_type)
    has_default = property(lambda self: self.__default is not None)

    @property
    def default(self):
        if self.__default is not None:
            if self.__sequence_type is None:
                return self.__element_type(self.__default)
            return self.__sequence_type(self.__default)
        return None

    def validate(self, value):
        if self.__sequence_type is None:
            if not isinstance(value, self.__element_type):
                raise exceptions.TypeException(self.__element_type, type(value))
        else:
            if not is_sequence(value):
                raise exceptions.SequenceTypeException(type(value))
            for element in value:
                if not isinstance(element, self.__element_type):
                    raise exceptions.TypeException(self.__element_type, type(element))

    def update(self, value):
        if self.__sequence_type is not None:
            return value if isinstance(value, self.__sequence_type) else self.__sequence_type(value)
        return value

    def __hash__(self):
        return hash((
            self.__name, self.__element_type,
            type(None) if self.__sequence_type is None else self.__sequence_type,
            None if self.__default is None else (
                self.__default if self.__sequence_type is None else tuple(self.__default)
            )
        ))

    def __eq__(self, other):
        assert isinstance(other, PropertyType)
        if self.name != other.name or self.sequence_type is not other.sequence_type or self.type is not other.type:
            return False
        return other.has_default and self.default == other.default if self.has_default else not other.has_default

    def to_json_data(self):
        return {
            'name': self.__name,
            'type': self.__element_type.__name__,
            'sequence': None if self.__sequence_type is None else self.__sequence_type.__name__,
            'default': None if self.__default is None else self.default
        }

    @classmethod
    def from_json_data(cls, json_dict, **kwargs):
        return cls(json_dict['name'], _type_name_to_type[json_dict['type']],
                   None if json_dict['sequence'] is None else _sequence_type_name_to_type[json_dict['sequence']],
                   json_dict['default'])


class Property(object):
    __slots__ = {'__property_type', '__value'}

    def __init__(self, property_type, value=None):
        assert isinstance(property_type, PropertyType)
        if value is not None:
            property_type.validate(value)
            value = property_type.update(value)
        elif property_type.has_default:
            value = property_type.default
        self.__property_type = property_type
        self.__value = value

    type = property(lambda self: self.__property_type)
    name = property(lambda self: self.__property_type.name)
    value = property(lambda self: self.__value)

    def __eq__(self, other):
        assert isinstance(other, Property)
        return self.type == other.type and (
                (self.value is None and other.value is None)
                or (other.value is not None and self.value == other.value))

    def set(self, value):
        self.__property_type.validate(value)
        self.__value = self.__property_type.update(value)

    def clear(self):
        self.__value = self.__property_type.default if self.__property_type.has_default else None


class PropertyTypeDict(JSONCompatible):
    __slots__ = {'__property_types'}

    def __init__(self, property_types=()):
        assert is_sequence(property_types)
        self.__property_types = {}
        for property_type in property_types:
            self.add(property_type)

    def __contains__(self, property_name):
        assert isinstance(property_name, str)
        return property_name in self.__property_types

    def __getitem__(self, property_type_name):
        return self.__property_types[property_type_name]

    def __len__(self):
        return len(self.__property_types)

    def to_json_data(self):
        return [pt.to_json_data() for pt in self.__property_types.values()]

    @classmethod
    def from_json_data(cls, json_data, **kwargs):
        """
        :rtype: PropertyTypeDict
        """
        return cls(PropertyType.from_json_data(json_dict) for json_dict in json_data)

    def names(self):
        return self.__property_types.keys()

    def types(self):
        return self.__property_types.values()

    def add(self, property_type):
        assert isinstance(property_type, PropertyType)
        assert property_type.name not in self.__property_types
        self.__property_types[property_type.name] = property_type

    def remove(self, property_name):
        assert isinstance(property_name, str)
        self.__property_types.pop(property_name, None)

    def update(self, property_type):
        assert isinstance(property_type, PropertyType)
        self.__property_types[property_type.name] = property_type

    def add_new_type(self, name, element_type, sequence_type=None, default=None):
        assert isinstance(name, str) and name not in self.__property_types
        property_type = PropertyType(name=name, element_type=element_type, sequence_type=sequence_type, default=default)
        self.__property_types[property_type.name] = property_type
        return property_type

    def add_new_list_type(self, name, element_type, default=None):
        return self.add_new_type(name, element_type, list, default=default)

    def add_new_set_type(self, name, element_type, default=None):
        return self.add_new_type(name, element_type, set, default=default)

    def new_value(self, name, value=None):
        assert isinstance(name, str) and name in self.__property_types
        return Property(self.__property_types[name], value)


class PropertyDict(JSONCompatible):

    def __init__(self, property_type_set, **name_to_value):
        assert isinstance(property_type_set, PropertyTypeDict)
        self.__type_set = property_type_set
        self.__properties = {}  # type: dict{str, Property}
        for name, value in name_to_value.items():
            self[name] = value
        for property_type in self.__type_set.types():
            if property_type.name not in name_to_value and property_type.has_default:
                self[property_type.name] = property_type.default

    def __getitem__(self, name):
        return self.__properties[name].value if name in self.__properties else None

    def __setitem__(self, name, value):
        if name in self.__properties:
            self.__properties[name].set(value)
        else:
            self.__properties[name] = self.__type_set.new_value(name, value)

    def to_json_data(self):
        return {key: self.__properties[key].value for key in self.__properties}

    @classmethod
    def from_json_data(cls, json_data, property_type_set=None):
        return cls(property_type_set, **json_data)

    def is_defined(self, name):
        return name in self.__properties and self.__properties[name].value is not None

    def clear(self, name):
        if name in self.__properties:
            self.__properties[name].clear()
