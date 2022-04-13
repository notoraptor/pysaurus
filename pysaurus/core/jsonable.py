import re
import types
from typing import Callable, Dict

__fn_types__ = (
    types.FunctionType,
    types.MethodType,
    types.BuiltinMethodType,
    types.BuiltinFunctionType,
    types.ClassMethodDescriptorType,
    classmethod,
    property,
)

__regex_attribute__ = re.compile(r"^[a-z][a-zA-Z0-9_]*$")


def is_attribute(key, value):
    return __regex_attribute__.match(key) and not isinstance(value, __fn_types__)


class Type:
    """
    key = value
        name = key, type = type(value), default = value
    key: type = value
        name = key, type = type, default = value (validate with type)
    key: type
        name = key, type = type, no default: must receive a value
    key = None
        name = key, type = any, default = None
    key: type = None
        name = key, type = type, default = None (only values are validated with type)
    type: either
        type
            type ot attribute
        short: str
            short name of attribute
        (type, short) or (short, type)
            type and short name of attribute
            If one attribute has short name, then all attributes must have short names
    """

    __slots__ = ("name", "short", "type", "default")

    def __init__(self, name, typedef, *default):
        assert __regex_attribute__.match(name)
        if typedef is None:
            short, ktype = None, None
        elif isinstance(typedef, (tuple, list)):
            assert len(typedef) == 2
            v1, v2 = typedef
            if isinstance(v1, str):
                assert isinstance(v2, type)
                short, ktype = v1, v2
            else:
                assert isinstance(v1, type)
                assert isinstance(v2, str)
                short, ktype = v2, v1
        elif isinstance(typedef, str):
            short, ktype = typedef, None
        else:
            assert isinstance(typedef, type)
            short, ktype = None, typedef
        if default:
            assert len(default) == 1
            (default_value,) = default
            if ktype is None and default_value is not None:
                ktype = type(default_value)
        if short is not None:
            assert __regex_attribute__.match(short)
        self.name = name
        self.short = short
        self.type = ktype
        self.default = default

    def __str__(self):
        ret = self.name
        if self.short:
            ret += "(" + self.short + ")"
        ret += ": " + (self.type.__name__ if self.type else "Any")
        if self.default:
            ret += f" = {self.default[0]}"
        return ret

    def __call__(self, *args):
        if len(args) == 0:
            return None if self.accepts_none() else self.new()
        else:
            assert len(args) == 1
            (value,) = args
            if value is None:
                if not self.accepts_none():
                    raise ValueError(f"None forbidden for attribute: {self.name}")
                return None
            else:
                return self.validate(value)

    def accepts_none(self):
        return self.default and self.default[0] is None

    def new(self):
        if not self.default:
            raise ValueError(f"No default value available for attribute: {self.name}")
        return self.validate(self.default[0])

    def validate(self, value):
        if self.type and not isinstance(value, self.type):
            raise TypeError(f"expected type {self.type}, got {type(value)}")
        return value

    def to_dict(self, value):
        return self(value)


class JsonableType(Type):
    def __init__(self, name, typedef, *default):
        super().__init__(name, typedef, *default)
        if self.type is None:
            self.type = Jsonable
        else:
            assert issubclass(self.type, Jsonable)

    def validate(self, value):
        if isinstance(value, self.type):
            return value
        assert isinstance(value, dict), type(value)
        return self.type.from_dict(value)

    def to_dict(self, value):
        value = self(value)
        return None if value is None else value.to_dict()


def _get_type(key, annotation, *default):
    attribute_type = Type(key, annotation, *default)
    if issubclass(attribute_type.type, Jsonable):
        typedef = (
            attribute_type.type
            if attribute_type.short is None
            else (attribute_type.type, attribute_type.short)
        )
        attribute_type = JsonableType(
            attribute_type.name, typedef, *attribute_type.default
        )
    return attribute_type


class Shortener:
    __slots__ = ("__to_short", "__to_long", "to_short", "to_long")

    def __init__(self, long_to_short: Dict[str, str]):
        self.__to_short: Dict[str, str] = {}
        self.__to_long: Dict[str, str] = {}
        self.to_short: Callable[[str], str] = self._neutral
        self.to_long: Callable[[str], str] = self._neutral
        if long_to_short:
            self.__to_short = long_to_short
            self.__to_long = {short: long for long, short in long_to_short.items()}
            self.to_short = self._to_short
            self.to_long = self._to_long

    @classmethod
    def _neutral(cls, key: str) -> str:
        return key

    def _to_short(self, long: str) -> str:
        return self.__to_short[long]

    def _to_long(self, short: str) -> str:
        return self.__to_long[short]


def get_bases(bases: tuple):
    if not bases:
        return ()
    assert len(bases) == 1
    all_bases = bases[0].__mro__
    assert all_bases[-1] is object
    assert all_bases[-2] is Jsonable
    return all_bases[:-2]


def gen_get(namespace: dict, key: str):
    name_getter = f"get_{key}"
    if name_getter in namespace:
        return namespace.pop(name_getter)

    def getter(self):
        return self.__json__[key]

    getter.__name__ = name_getter

    return getter


def gen_set(namespace: dict, key: str):
    name_setter = f"set_{key}"

    if name_setter in namespace:
        return namespace.pop(name_setter)

    def setter(self, value):
        self.__json__[key] = value

    setter.__name__ = name_setter

    return setter


class _MetaJSON(type):
    __slots__ = ()

    def __new__(mcs, name, bases, namespace):
        assert "__definitions__" not in namespace, "Reserved attribute: __definitions__"
        annotations = namespace.get("__annotations__", {})
        attributes = {
            key: value for key, value in namespace.items() if is_attribute(key, value)
        }
        original_attributes = list(attributes)
        definitions = {}
        for base in get_bases(bases):
            definitions.update(base.__definitions__)
        for key, value in attributes.items():
            if isinstance(value, Type):
                assert key not in annotations
                definitions[key] = value
            elif key in annotations:
                annotation = annotations[key]
                definitions[key] = _get_type(key, annotation, value)
            else:
                definitions[key] = _get_type(key, None, value)
        for key, annotation in annotations.items():
            if key not in definitions:
                original_attributes.append(key)
                definitions[key] = _get_type(key, annotation)
        short = {jt.name: jt.short for jt in definitions.values() if jt.short}
        if short:
            assert len(short) == len(definitions), "short required for all or nothing"
        else:
            short = namespace.get("__short__", {})
        namespace["__definitions__"] = {
            key: definitions[key] for key in sorted(definitions)
        }
        namespace["__shortener__"] = Shortener(short)
        for key in original_attributes:
            namespace[key] = property(gen_get(namespace, key), gen_set(namespace, key))
        return type.__new__(mcs, name, bases, namespace)


class Jsonable(metaclass=_MetaJSON):
    __slots__ = ("__json__",)

    def __init__(self, **kwargs):
        self.__json__ = {}
        for key, checker in self.__definitions__.items():
            if key in kwargs:
                value = checker(kwargs.pop(key))
            else:
                value = checker()
            self.__json__[key] = value
        if kwargs:
            raise KeyError(kwargs)

    def __bool__(self):
        return True

    def __len__(self):
        return len(self.__json__)

    def __iter__(self):
        return iter(self.__json__.items())

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        return (
            isinstance(other, Jsonable)
            and len(self) == len(other)
            and all(a == b for a, b in zip(self, other))
        )

    def __str__(self):
        fields = ", ".join(
            f"{key}={repr(value) if isinstance(value, str) else value}"
            for key, value in self
        )
        return f"{type(self).__name__}({fields})"

    __repr__ = __str__

    def update(self, dct: dict):
        assert isinstance(dct, dict)
        for key, checker in self.__definitions__.items():
            if key in dct:
                self.__json__[key] = checker(dct[key])

    @classmethod
    def get_args_from(cls, dictionary: dict):
        return {field: dictionary[field] for field in cls.__definitions__}

    def to_json(self):
        return self.__json__

    @classmethod
    def from_json(cls, dct):
        assert isinstance(dct, dict)
        return cls(**dct)

    def to_dict(self):
        return {
            self.__shortener__.to_short(key): self.__definitions__[key].to_dict(value)
            for key, value in self
        }

    @classmethod
    def from_dict(cls, dct):
        assert isinstance(dct, dict)
        return cls(
            **{cls.__shortener__.to_long(short): value for short, value in dct.items()}
        )
