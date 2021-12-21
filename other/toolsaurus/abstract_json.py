import typing

from other.toolsaurus.functions import assert_str
from pysaurus.core import classes


class Object:
    __slots__ = "name", "default"

    def __init__(self, name: str, default=None):
        self.name = name
        self.default = default

    def __call__(self, value=None):
        if value is None:
            return self.new()
        assert self.is_instance(
            value
        ), f"Expected {type(self).__name__}, got {type(value).__name__}:{value}"
        return self.ensure(value)

    def is_instance(self, value):
        return True

    def ensure(self, value):
        return value

    def new(self):
        return self.default


class _Builtin(Object):
    __slots__ = ()
    __type__ = object

    def __init__(self, name, default=None):
        super().__init__(
            name, self.__type__() if default is None else self.__type__(default)
        )

    def is_instance(self, value):
        return isinstance(value, self.__type__)


class Sequence(Object):
    __slots__ = ()

    def __init__(self, name, default=()):
        super().__init__(name, sorted(default))

    def is_instance(self, value):
        return isinstance(value, (tuple, list, set))

    def ensure(self, value):
        return sorted(value)

    def new(self):
        return list(self.default)


class Null(Object):
    __slots__ = ()

    def __init__(self, name):
        super().__init__(name)

    def is_instance(self, value):
        return value is None


class Bool(_Builtin):
    __slots__ = ()
    __type__ = bool


class Float(_Builtin):
    __slots__ = ()
    __type__ = float


class Int(_Builtin):
    __slots__ = ()
    __type__ = int


class Dict(_Builtin):
    __slots__ = ()
    __type__ = dict

    def new(self):
        return {**self.default}


class Str(_Builtin):
    __slots__ = ()
    __type__ = str


class Text(Str):
    __slots__ = ()

    def __init__(self, name, default=""):
        super().__init__(name, default)

    def ensure(self, value):
        return classes.Text(value)

    def new(self):
        return classes.Text(self.default)


def _json_derived(dependencies: dict):
    derived = set()
    for base_derived in dependencies.values():
        derived.update(base_derived)
    return derived


class _JSONScheme:
    def __init__(self):
        self.scheme = []

    def __call__(self, definition):
        definition = (
            definition
            if isinstance(definition, Object)
            else Object(assert_str(definition))
        )
        self.scheme.append(definition)
        return property(lambda obj: obj.__json__[definition.name])

    def __iter__(self):
        return self.scheme.__iter__()

    def sequence(self, name, default=()):
        return self(Sequence(name, default))

    def null(self, name):
        return self(Null(name))

    def bool(self, name, default=None):
        return self(Bool(name, default))

    def float(self, name, default=None):
        return self(Float(name, default))

    def int(self, name, default=None):
        return self(Int(name, default))

    def dict(self, name, default=None):
        return self(Dict(name, default))

    def str(self, name, default=None):
        return self(Str(name, default))

    def text(self, name, default=None):
        return self(Text(name, default))


class _JSONDepends(typing.Dict[str, typing.Set[str]]):
    __slots__ = ()

    def __call__(self, *dependencies: str):
        def decorator(fn):
            derived = fn.__name__
            for base in dependencies:
                self.setdefault(base, set()).add(derived)
            return property(fn)

        return decorator


class AbstractJSON:
    __slots__ = ("__json__",)
    __scheme__ = ()  # type: typing.Sequence[Object]
    __depends__ = {}

    def __init__(self, **kwargs):
        self.__json__ = {
            definition.name: definition(kwargs.get(definition.name, None))
            for definition in self.__scheme__
        }
        for derived in _json_derived(self.__depends__):
            self.__json__[derived] = getattr(self, derived)

    def get(self, name):
        return self.__json__[name]

    def set(self, base, value):
        assert base in self.__json__
        self.__json__[base] = value
        for derived in self.__depends__.get(base, ()):
            self.__json__[derived] = getattr(self, derived)

    @staticmethod
    def Scheme():
        return _JSONScheme()

    @staticmethod
    def Depends():
        return _JSONDepends()


class Test(AbstractJSON):
    __slots__ = ()
    __scheme__ = AbstractJSON.Scheme()
    __depends__ = AbstractJSON.Depends()
    a = __scheme__.str("a")
    b = __scheme__.int("b")
    c = __scheme__.float("c", 233)

    @__depends__("c", "b")
    def special(self):
        return self.b * self.c


def main():
    test = Test(b=-7, c=68.0)
    print(test.a)
    print(test.b)
    print(test.c)
    print(test.__json__)
    test.set("c", 1)
    print(test.__json__)


if __name__ == "__main__":
    main()
