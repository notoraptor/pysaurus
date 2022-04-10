import types
from typing import Dict, Sequence

from pysaurus.core.functions import is_valid_attribute_name

__fn_types__ = (
    types.FunctionType,
    types.MethodType,
    types.BuiltinMethodType,
    types.BuiltinFunctionType,
    types.ClassMethodDescriptorType,
    classmethod,
)


def is_attribute(key, value):
    return is_valid_attribute_name(key) and not isinstance(value, __fn_types__)


class _Checker:
    __slots__ = ("default",)

    def __init__(self, *args):
        if len(args) == 0:
            self.default = ()
        else:
            assert len(args) == 1
            (value,) = args
            self.default = None if value is None else (value,)

    def __call__(self, *args):
        if len(args) == 0:
            return None if self.default is None else self.validate(*self.default)
        else:
            assert len(args) == 1
            (value,) = args
            return None if value is self.default is None else self.validate(value)

    def __str__(self):
        return f"${type(self).__name__}" f"({', '.join(str(d) for d in self.default)})"

    __repr__ = __str__

    def validate(self, *args):
        raise NotImplementedError()

    def to_dict(self, value):
        return value


class _ClassChecker(_Checker):
    __slots__ = ("cls",)

    def __init__(self, cls, *args):
        assert isinstance(cls, type)
        super().__init__(*args)
        self.cls = cls

    def validate(self, *args):
        if len(args) == 0:
            return self.cls()
        else:
            assert len(args) == 1
            (value,) = args
            return value if isinstance(value, self.cls) else self.cls(value)


class _JsonableChecker(_Checker):
    __slots__ = ("cls",)

    def __init__(self, cls, *args):
        assert issubclass(cls, Jsonable)
        if args:
            (default,) = args
            if isinstance(default, cls):
                default = default.to_dict()
            else:
                assert isinstance(default, dict) or default is None
        else:
            default = {}
        super().__init__(default)
        self.cls = cls

    def validate(self, *args):
        if len(args) == 0:
            return super().validate()
        else:
            assert len(args) == 1
            (value,) = args
            return value if isinstance(value, self.cls) else self.cls.from_dict(value)

    def to_dict(self, value):
        return value.to_dict()


def _get_checker(cls, *args):
    if issubclass(cls, Jsonable):
        return _JsonableChecker(cls, *args)
    else:
        return _ClassChecker(cls, *args)


class ShortFunctor:
    __slots__ = ("__to_short", "__to_long")

    def __init__(self, fields: Sequence[str], long_to_short: Dict[str, str]):
        assert len(fields) == len(long_to_short)
        assert all(field in long_to_short for field in fields)
        self.__to_short = long_to_short
        self.__to_long = {short: long for long, short in long_to_short.items()}

    def to_short(self, dct_long_keys: dict):
        return {self.__to_short[key]: value for key, value in dct_long_keys.items()}

    def from_short(self, dct_short_keys: dict):
        return {self.__to_long[short]: value for short, value in dct_short_keys.items()}


class NoShortFunctor:
    __slots__ = ()

    @classmethod
    def to_short(cls, dct):
        return dct

    @classmethod
    def from_short(cls, dct):
        return dct


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

    def __new__(cls, name, bases, namespace):
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
            if isinstance(value, _Checker):
                assert key not in annotations
                definitions[key] = value
            elif key in annotations:
                annotation = annotations[key]
                assert isinstance(annotation, type)
                definitions[key] = _get_checker(annotation, value)
            else:
                definitions[key] = _get_checker(type(value), value)
        for key, annotation in annotations.items():
            if key not in definitions:
                original_attributes.append(key)
                assert isinstance(annotation, type)
                definitions[key] = _get_checker(annotation)
        short = namespace.get("__short__", {})
        shortener = (
            ShortFunctor(tuple(definitions), short) if short else NoShortFunctor()
        )
        namespace["__definitions__"] = {
            key: definitions[key] for key in sorted(definitions)
        }
        namespace["__shortener__"] = shortener
        for key in original_attributes:
            namespace[key] = property(gen_get(namespace, key), gen_set(namespace, key))
        return type.__new__(cls, name, bases, namespace)


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
        return type(self) is type(other) and all(a == b for a, b in zip(self, other))

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

    def to_json(self):
        return self.__json__

    @classmethod
    def from_json(cls, dct):
        assert isinstance(dct, dict)
        return cls(**dct)

    def to_dict(self):
        return self.__shortener__.to_short(
            {key: self.__definitions__[key].to_dict(value) for key, value in self}
        )

    @classmethod
    def from_dict(cls, dct):
        assert isinstance(dct, dict)
        return cls(**cls.__shortener__.from_short(dct))
