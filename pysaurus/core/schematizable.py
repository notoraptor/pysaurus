from typing import Any, Dict, Iterable

from pysaurus.core.jsonable import Type


class Schema:
    __slots__ = ("schema",)

    def __init__(self, types: Iterable[Type]):
        self.schema: Dict[str, Type] = {t.name: t for t in types}

    def get_from_short_dict(self, data: dict, name: str):
        tp = self.schema[name]
        sh = tp.short
        if sh in data:
            value = tp.from_dict(tp.type, data[sh])
        else:
            value = tp()
        return value

    def set_into_short_dict(self, data: dict, name: str, value: Any):
        tp = self.schema[name]
        data[tp.short] = value

    def has_in_short_dict(self, data: dict, name: str):
        tp = self.schema[name]
        return tp.short in data

    def get_short_key(self, name):
        return self.schema[name].short


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


class WithSchema:
    __slots__ = ("_d",)
    SCHEMA = Schema(())

    def __init__(self, short_dict: dict, **kwargs):
        self._d = short_dict

    def _get(self, name):
        return self.SCHEMA.get_from_short_dict(self._d, name)

    def _set(self, name, value):
        self.SCHEMA.set_into_short_dict(self._d, name, value)

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
            **other_kwargs
        )


def schema_prop(name):
    return property(lambda self: self._get(name), lambda self, v: self._set(name, v))
