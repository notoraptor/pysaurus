from abc import ABCMeta

from typing import Iterable

SIMPLE_TYPES = (str, bool, int, float)
COMPLEX_TYPES = (tuple, list, set, dict)
TYPES = (*SIMPLE_TYPES, *COMPLEX_TYPES)

_Type = str | bool | int | float | tuple | list | set | dict


class UnsupportedTypeError(Exception):
    def __init__(self, value, prefix=""):
        super().__init__(f"{prefix}: {value}" if prefix else value)


def _check(data: _Type | None, *, prefix: str = "") -> _Type | None:
    if isinstance(data, COMPLEX_TYPES):
        if isinstance(data, dict):
            for key, value in data.items():
                if not isinstance(key, str):
                    raise UnsupportedTypeError(key, prefix=prefix + ".key")
                _check(value, prefix=prefix + f"[{key!r}]")
        else:
            for i, value in enumerate(data):
                _check(
                    value,
                    prefix=prefix + f"{'.set' if isinstance(data, set) else ''}[{i}]",
                )
    elif data is not None and not isinstance(data, SIMPLE_TYPES):
        raise UnsupportedTypeError(data, prefix=prefix)
    return data


class _RomData(metaclass=ABCMeta):
    __slots__ = ()

    def dump(self) -> _Type | None:
        raise NotImplementedError


class _RomSequence(_RomData):
    pass


class _RomList(_RomSequence):
    pass


class _RomTuple(_RomSequence):
    pass


class _RomSet(_RomSequence):
    pass


class _RomDict(_RomData):
    pass


class _RomConst(_RomData):
    def __init__(self, value: _Type | None):
        assert value is None or isinstance(value, SIMPLE_TYPES)
        self.__value = value

    def dump(self):
        return self.__value


class Rom:
    def __init__(self, path: str = ".rom"):
        self.__path: str = path
        self.__env: dict[str, _RomData] = {}
        self.__in_context: bool = False

        self.__load()

    def __enter__(self):
        self.__in_context = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__in_context = False
        self.save()

    def __getitem__(self, key):
        pass

    def __setitem__(self, key: str, value: _Type):
        pass

    def tuple(self, elements: Iterable) -> _RomTuple:
        return _RomTuple(elements)

    def list(self, elements: Iterable) -> _RomList:
        return _RomList(elements)

    def set(self, elements: Iterable) -> _RomSet:
        return _RomSet(elements)

    def dict(self, dictionary: dict) -> _RomDict:
        return _RomDict(dictionary)

    def save(self):
        self.__save()

    def __load(self):
        pass

    def __save(self):
        pass
