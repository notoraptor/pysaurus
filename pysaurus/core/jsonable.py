import re
import types
from typing import Sequence, Dict

from pysaurus.core.override import Override

REGEX_ATTRIBUTE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")

__fn_types__ = (
    types.FunctionType,
    types.MethodType,
    types.BuiltinMethodType,
    types.BuiltinFunctionType,
    types.ClassMethodDescriptorType,
    classmethod,
)


def is_attribute(key, value):
    return REGEX_ATTRIBUTE.match(key) and not isinstance(value, __fn_types__)


class _Checker:
    __slots__ = ("default",)

    __init__ = Override("_Checker.__init__")

    @__init__.override
    def __init__(self):
        self.default = ()

    @__init__.override
    def __init__(self, value: object):
        self.default = None if value is None else (value,)

    __call__ = Override("_Checker.__call__")

    @__call__.override
    def __call__(self):
        return None if self.default is None else self.validate(*self.default)

    @__call__.override
    def __call__(self, value: object):
        return None if value is self.default is None else self.validate(value)

    def __str__(self):
        return f"${type(self).__name__}" f"({', '.join(str(d) for d in self.default)})"

    __repr__ = __str__

    validate = Override("_Checker.validate")

    @validate.override
    def validate(self):
        raise NotImplementedError()

    @validate.override
    def validate(self, value: object):
        raise NotImplementedError()

    def to_json(self, value):
        return value


class _ClassChecker(_Checker):
    __slots__ = ("cls",)

    def __init__(self, cls, *args):
        assert isinstance(cls, type)
        super().__init__(*args)
        self.cls = cls

    @_Checker.validate.override
    def validate(self):
        return self.cls()

    @_Checker.validate.override
    def validate(self, value: object):
        return value if isinstance(value, self.cls) else self.cls(value)


class _JsonableChecker(_Checker):
    __slots__ = ("cls",)

    def __init__(self, cls, *args):
        assert issubclass(cls, Jsonable)
        if args:
            (default,) = args
            if isinstance(default, cls):
                default = default.to_json()
            else:
                assert isinstance(default, dict) or default is None
        else:
            default = {}
        super().__init__(default)
        self.cls = cls

    @_Checker.validate.override
    def validate(self, value: object):
        return value if isinstance(value, self.cls) else self.cls.from_json(value)

    def to_json(self, value):
        return value.to_json()


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


class _MetaJSON(type):
    def __init__(self, name, bases, namespace, **kwargs):
        assert "__definitions__" not in namespace, "Reserved attribute: __definitions__"
        super().__init__(name, bases, namespace, **kwargs)
        annotations = namespace.get("__annotations__", {})
        attributes = {
            key: value for key, value in namespace.items() if is_attribute(key, value)
        }
        definitions = {}
        for base in bases:
            if type(base) is type(self):
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
                assert isinstance(annotation, type)
                definitions[key] = _get_checker(annotation)
        short = namespace.get("__short__", {})
        shortener = (
            ShortFunctor(tuple(definitions), short) if short else NoShortFunctor()
        )
        self.__definitions__ = {key: definitions[key] for key in sorted(definitions)}
        self.__shortener__ = shortener


class Jsonable(metaclass=_MetaJSON):
    __slots__ = ()

    def __init__(self, **kwargs):
        for key, checker in self.__definitions__.items():
            if key in kwargs:
                value = checker(kwargs.pop(key))
            else:
                value = checker()
            setattr(self, key, value)
        assert not kwargs, f"{type(self).__name__}: unknown keys: {tuple(kwargs)}"

    def __bool__(self):
        return True

    def __len__(self):
        return len(self.__definitions__)

    def __iter__(self):
        return iter((key, getattr(self, key)) for key in self.__definitions__)

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
        for key, checker in self.__definitions__.items():
            if key in dct:
                setattr(self, key, checker(dct[key]))

    def to_json(self):
        return self.__shortener__.to_short(
            {key: self.__definitions__[key].to_json(value) for key, value in self}
        )

    @classmethod
    def from_json(cls, dct):
        assert isinstance(dct, dict)
        return cls(**cls.__shortener__.from_short(dct))

    to_dict = to_json
    from_dict = from_json
