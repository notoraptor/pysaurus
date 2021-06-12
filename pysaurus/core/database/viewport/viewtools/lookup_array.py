from typing import Generic, Iterable, TypeVar, Type, List, Dict, Any, Callable

T = TypeVar("T")


class LookupArray(Generic[T]):
    __slots__ = "__type", "__content", "__table", "__key_fn"

    def __init__(self, element_type, content: Iterable[T] = (), key: callable = None):
        self.__type = element_type  # type: Type
        self.__content = []  # type: List[T]
        self.__table = {}  # type: Dict[Any, int]
        self.__key_fn = (
            key if callable(key) else lambda value: value
        )  # type: Callable[[T], Any]
        self.extend(content)

    def __str__(self):
        return "%s<%s>%s" % (type(self).__name__, self.__type.__name__, self.__content)

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
        self.__content.append(value)
        self.__table[self.__key_fn(value)] = len(self.__content) - 1

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
