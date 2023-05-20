from typing import Any, Dict, Iterable

from pysaurus.core.json_type import Type


class SchemaType(Type):
    def __init__(self, name, typedef, *default):
        super().__init__(name, typedef, *default)
        if self.type is None:
            self.type = WithSchema
        else:
            assert issubclass(self.type, WithSchema), self.type

    def validate(self, value):
        return value if isinstance(value, self.type) else self.type.from_dict(value)

    def new(self):
        return self.validate(super().new())

    def standard_to_dict(self, obj, value):
        value = self(value)
        return None if value is None else value.to_dict()

    def standard_from_dict(self, cls, value):
        return None if value is None else self.type.from_dict(value)

    def to_linear(self):
        return [self.short, self.type.SCHEMA.to_linear_type()]


class Schema:
    __slots__ = ("schema", "from_short", "linear_type")

    def __init__(self, types: Iterable[Type]):
        self.schema: Dict[str, Type] = {t.name: t for t in types}
        self.from_short = {t.short: t.name for t in self.schema.values()}
        self.linear_type = self.to_linear_type()

    def get_from_short_dict(self, data: dict, name: str):
        tp = self.schema[name]
        sh = tp.short
        if sh in data:
            value = tp.from_dict(tp.type, data[sh])
        else:
            value = tp()
        return value

    def set_into_short_dict(self, data: dict, name: str, value: Any) -> bool:
        short = self.schema[name].short
        modified = short not in data or data[short] != value
        if modified:
            data[short] = value
        return modified

    def has_in_short_dict(self, data: dict, name: str):
        tp = self.schema[name]
        return tp.short in data

    def get_short_key(self, name):
        return self.schema[name].short

    def to_long_keys(self, short_dict: dict):
        return {self.from_short[key]: value for key, value in short_dict.items()}

    def to_linear_type(self):
        return [self.schema[name].to_linear() for name in sorted(self.schema)]

    @staticmethod
    def short_dict_to_linear(d: dict, linear_type: list) -> list:
        return [
            (Schema.short_dict_to_linear(d[short], desc) if desc else d[short])
            if short in d
            else None
            for short, desc in linear_type
        ]

    @staticmethod
    def linear_to_short_dict(linear_type: list, linear_value: list) -> dict:
        return {
            short: (Schema.linear_to_short_dict(desc, value) if desc else value)
            for ((short, desc), value) in zip(linear_type, linear_value)
            if value is not None
        }


class WithSchema:
    __slots__ = ("_d",)
    SCHEMA = Schema(())

    def __init__(self, short_dict: dict = None, **kwargs):
        self._d = short_dict or {}

    def __str__(self):
        return f"{type(self).__name__}({self._d})"

    def _get(self, name):
        return self.SCHEMA.get_from_short_dict(self._d, name)

    def _set(self, name, value) -> bool:
        return self.SCHEMA.set_into_short_dict(self._d, name, value)

    def _has(self, name):
        return self.SCHEMA.has_in_short_dict(self._d, name)

    @classmethod
    def ensure_short_keys(cls, dct: dict, keys_are_short: bool):
        return (
            dct
            if keys_are_short
            else {cls.SCHEMA.get_short_key(key): value for key, value in dct.items()}
        )

    def to_dict(self):
        return self._d

    @classmethod
    def from_dict(cls, dct: dict, **kwargs):
        return cls(short_dict=dct, **kwargs)

    def _to_linear(self):
        return Schema.short_dict_to_linear(self._d, self.SCHEMA.linear_type)

    @classmethod
    def _from_linear(cls, linear: list, **kwargs):
        return cls.from_dict(
            Schema.linear_to_short_dict(cls.SCHEMA.linear_type, linear), **kwargs
        )

    @classmethod
    def from_keys(cls, **kwargs):
        key_kwargs = {}
        other_kwargs = {}
        for name, value in kwargs.items():
            if name in cls.SCHEMA.schema:
                key_kwargs[name] = value
            else:
                other_kwargs[name] = value
        return cls(
            short_dict={
                cls.SCHEMA.get_short_key(name): value
                for name, value in key_kwargs.items()
            },
            **other_kwargs,
        )


def schema_prop(name):
    return property(lambda self: self._get(name), lambda self, v: self._set(name, v))
