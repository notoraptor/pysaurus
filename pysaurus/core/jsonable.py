import re
import types
from copy import deepcopy
from typing import Any, Callable, Dict, Iterable

__fn_types__ = (
    types.FunctionType,
    types.MethodType,
    types.BuiltinMethodType,
    types.BuiltinFunctionType,
    types.ClassMethodDescriptorType,
    classmethod,
    staticmethod,
    property,
)

__regex_attribute__ = re.compile(r"^[a-z][a-zA-Z0-9_]*$")
__regex_short__ = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")


def is_attribute(key, value):
    return __regex_attribute__.match(key) and not isinstance(value, __fn_types__)


class Type:
    """
    name: typedef = default
        name: string, required
        typedef: optional, attribute type (`type`) and short name (`str`). Either:
            type: attribute type (short name set to None)
            short: attribute short name (type set to default's type)
            (type, short) or (short, type): attribute type and short name
        default: optional
            If not provided:
                No default allowed: value required for this attribute.
                If type not provided, any type allowed.
            If None:
                None allowed as value.
                If type not provided, any type allowed.
            If provided:
                Will be validated against attribute type
                If type not provided, type is default's type
    NB: If one attribute has short name, then all attributes must have short names
    """

    __slots__ = (
        "name",
        "short",
        "type",
        "default",
        "to_dict",
        "from_dict",
        "allowed_types",
        "_get_default",
    )

    def __init__(self, name, typedef, *default):
        assert __regex_attribute__.match(name)
        if typedef is None:
            short, ktype = None, None
        elif isinstance(typedef, (tuple, list)):
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
            (default_value,) = default
            if ktype is None and default_value is not None:
                ktype = type(default_value)
        if short is not None:
            assert __regex_short__.match(short)
        self.name = name
        self.short = short
        self.type = ktype
        self.default = default
        self.to_dict = self.standard_to_dict
        self.from_dict = self.standard_from_dict
        self.allowed_types = None
        self._get_default = None
        if self.type:
            self.allowed_types = (int, float) if self.type is float else (self.type,)

    def __str__(self):
        ret = self.name + (f"({self.short})" if self.short else "")
        ret += ": " + (self.type.__name__ if self.type else "Any")
        ret += f" = {self.default[0]}" if self.default else ""
        return ret

    def __call__(self, *args):
        if len(args) == 0:
            return None if self.accepts_none() else self.new()
        else:
            (value,) = args
            if value is None:
                if not self.accepts_none():
                    raise ValueError(f"None forbidden for attribute: {self.name}")
                return None
            else:
                return self.validate(value)

    def _get_immutable_default(self):
        return self.default[0]

    def _get_mutable_default(self):
        return deepcopy(self.default[0])

    def accepts_none(self):
        return self.default and self.default[0] is None

    def new(self):
        if not self.default:
            raise ValueError(f"No default value available for attribute: {self.name}")
        if self._get_default is None:
            self(self.default[0])
            if isinstance(self.default[0], (bool, int, float, str, bytes)):
                self._get_default = self._get_immutable_default
            else:
                self._get_default = self._get_mutable_default
        return self._get_default()

    def validate(self, value):
        if self.allowed_types and not isinstance(value, self.allowed_types):
            raise TypeError(
                f"{self.name}: type error, "
                f"expected {self.allowed_types}, got {type(value)}"
            )
        return value

    def standard_to_dict(self, obj, value):
        return self(value)

    def standard_from_dict(self, cls, value):
        return self(value)


class JsonableType(Type):
    def __init__(self, name, typedef, *default):
        super().__init__(name, typedef, *default)
        if self.type is None:
            self.type = Jsonable
        else:
            assert issubclass(self.type, Jsonable)

    def validate(self, value):
        return value if isinstance(value, self.type) else self.type.from_dict(value)

    def new(self):
        return self.validate(super().new())

    def standard_to_dict(self, obj, value):
        value = self(value)
        return None if value is None else value.to_dict()

    def standard_from_dict(self, cls, value):
        return None if value is None else self.type.from_dict(value)


def _get_type(key, annotation, *default):
    attr_t = Type(key, annotation, *default)
    if issubclass(attr_t.type, Jsonable):
        attr_t = JsonableType(
            attr_t.name,
            (attr_t.type if attr_t.short is None else (attr_t.type, attr_t.short)),
            *attr_t.default,
        )
    return attr_t


class Shortener:
    __slots__ = ("__to_short", "__to_long", "to_short", "from_short")

    def __init__(self, long_to_short: Dict[str, str]):
        self.__to_short: Dict[str, str] = {}
        self.__to_long: Dict[str, str] = {}
        self.to_short: Callable[[str], str] = self._neutral
        self.from_short: Callable[[str], str] = self._neutral
        if long_to_short:
            self.__to_short = long_to_short
            self.__to_long = {short: long for long, short in long_to_short.items()}
            self.to_short = self._to_short
            self.from_short = self._to_long

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


def generate_property(
    namespace: Dict[str, Any], key: str, previous_properties: Dict[str, property]
):
    getter = None
    setter = None
    prev_prop = None
    if key in previous_properties:
        prev_prop = previous_properties[key]
        getter = prev_prop.fget
        setter = prev_prop.fset

    name_getter = f"_get_{key}"
    if name_getter in namespace:
        getter = namespace.pop(name_getter)
    elif getter is None:

        def fn_get(self):
            return self.__json__[key]

        fn_get.__name__ = name_getter
        getter = fn_get

    name_setter = f"_set_{key}"
    if name_setter in namespace:
        setter = namespace.pop(name_setter)
    elif setter is None:

        def fn_set(self, value):
            self.__json__[key] = value

        fn_set.__name__ = name_setter
        setter = fn_set

    if prev_prop and prev_prop.fget is getter and prev_prop.fset is setter:
        return prev_prop
    else:
        return property(getter, setter)


class _MetaJSON(type):
    __slots__ = ()

    def __new__(mcs, name, bases, namespace):
        assert "__definitions__" not in namespace, "Reserved attribute: __definitions__"
        assert "__shortener__" not in namespace, "Reserved attribute: __shortener__"

        annotations = namespace.get("__annotations__", {})
        attributes = {
            key: value for key, value in namespace.items() if is_attribute(key, value)
        }
        original_attributes = list(attributes)
        definitions: Dict[str, Type] = {}
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
        short = {
            jt.name: jt.short for jt in definitions.values() if jt.short
        } or namespace.get("__short__", {})
        if short:
            if len(short) != len(definitions):
                raise TypeError(
                    f"short required for all or nothing.\n"
                    f"Got:      {', '.join(sorted(short))}\n"
                    f"Expected: {', '.join(sorted(definitions))}"
                )
            assert all(
                key in short for key in definitions
            ), "missing attributes in short"
            assert len(short) == len(set(short.values())), "Found common short names"

        for jt in definitions.values():
            name_to_dict = f"_to_dict_{jt.name}"
            name_from_dict = f"_from_dict_{jt.name}"
            if name_to_dict in namespace:
                jt.to_dict = namespace.pop(name_to_dict)
                if isinstance(jt.to_dict, (classmethod, staticmethod)):
                    jt.to_dict = jt.to_dict.__func__
                assert callable(jt.to_dict)
            if name_from_dict in namespace:
                jt.from_dict = namespace.pop(name_from_dict)
                if isinstance(jt.from_dict, (classmethod, staticmethod)):
                    jt.from_dict = jt.from_dict.__func__
                assert callable(jt.from_dict)

        prev_properties = {}
        for base in reversed(get_bases(bases)):  # from ancient to recent base
            for key in definitions:
                if hasattr(base, key):
                    prev_properties[key] = getattr(base, key)
        assert all(isinstance(value, property) for value in prev_properties.values())

        namespace["__definitions__"] = {
            key: definitions[key] for key in sorted(definitions)
        }
        namespace["__shortener__"] = Shortener(short)
        for key in definitions:
            namespace[key] = generate_property(namespace, key, prev_properties)
        return type.__new__(mcs, name, bases, namespace)


class Jsonable(metaclass=_MetaJSON):
    __slots__ = ("__json__",)

    def __init__(self, **kwargs):
        self.__json__ = {
            key: chk(kwargs[key]) if key in kwargs else chk()
            for key, chk in self.__definitions__.items()
        }

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

    def update(self, dct: dict) -> Dict[str, Any]:
        old_modified = {}
        for key, value in dct.items():
            value = self.__definitions__[key](value)
            if self.__json__[key] != value:
                old_modified[key] = self.__json__[key]
                self.__json__[key] = value
        return old_modified

    def match_json(self, **kwargs) -> bool:
        return all(
            self.__json__[key] == self.__definitions__[key](value)
            for key, value in kwargs.items()
        )

    def extract_attributes(self, keys: Iterable[str]) -> Dict[str, Any]:
        return {key: getattr(self, key) for key in keys}

    @classmethod
    def get_args_from(cls, dictionary: dict):
        return {field: dictionary[field] for field in cls.__definitions__}

    def to_json(self):
        return self.__json__

    @classmethod
    def from_json(cls, dct: dict):
        return cls(**dct)

    def to_dict(self):
        return {
            self.__shortener__.to_short(key): self.__definitions__[key].to_dict(
                self, value
            )
            for key, value in self
        }

    @classmethod
    def from_dict(cls, dct: dict, **kwargs):
        params = {}
        for short, value in dct.items():
            key = cls.__shortener__.from_short(short)
            params[key] = cls.__definitions__[key].from_dict(cls, value)
        return cls(**params, **kwargs)
