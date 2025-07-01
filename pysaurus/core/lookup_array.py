from typing import Any, Callable, Generic, Iterable, Sequence, Type, TypeVar

T = TypeVar("T")


class LookupArray(Generic[T]):
    __slots__ = "__type", "__content", "__table", "__key_fn"

    def __init__(
        self,
        element_type: Type | Sequence[Type],
        content: Iterable[T] = (),
        key: Callable[[T], Any] = None,
    ):
        self.__type: Type | Sequence[Type] = element_type
        self.__content: list[T] = []
        self.__table: dict[Any, int] = {}
        self.__key_fn: Callable[[T], Any] = (
            key if callable(key) else lambda value: value
        )
        self.extend(content)

    def __str__(self):
        return f"{type(self).__name__}<{self.__type}>{self.__content}"

    __repr__ = __str__

    def __len__(self):
        return len(self.__content)

    def __getitem__(self, item):
        return self.__content[item]

    def __iter__(self):
        return self.__content.__iter__()

    def __reversed__(self):
        return self.__content.__reversed__()

    def __contains__(self, value: T):
        return isinstance(value, self.__type) and self.__key_fn(value) in self.__table

    def __check_type(self, value):
        assert value is None or isinstance(value, self.__type), value

    def extend(self, iterable):
        for element in iterable:
            self.append(element)

    def append(self, value: T):
        self.__check_type(value)
        key = self.__key_fn(value)
        assert key not in self.__table, (value, key)
        self.__content.append(value)
        self.__table[key] = len(self.__content) - 1

    def pop(self, index: int):
        if index < 0:
            index = len(self.__content) + index
        value = self.__content.pop(index)
        assert index == self.__table.pop(self.__key_fn(value))
        for i in range(index, len(self.__content)):
            self.__table[self.__key_fn(self.__content[i])] = i
        return value

    def remove(self, value: T):
        self.__check_type(value)
        self.pop(self.__table[self.__key_fn(value)])

    def lookup(self, key) -> T:
        return self.__content[self.__table[key]]

    def lookup_index(self, key):
        return self.__table[key]

    def contains_key(self, key):
        return key in self.__table

    def keys(self):
        return self.__table.keys()

    def clear(self):
        self.__content.clear()
        self.__table.clear()
