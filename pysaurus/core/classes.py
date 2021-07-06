import locale
from abc import abstractmethod
from io import StringIO
from itertools import chain
from typing import Any, Generic, List, TypeVar

T = TypeVar("T")


class StringPrinter:
    __slots__ = "__string_buffer", "__strip_right"

    def __init__(self, strip_right=True):
        self.__string_buffer = StringIO()
        self.__strip_right = bool(strip_right)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__string_buffer.close()

    def __str__(self):
        return (
            self.__string_buffer.getvalue().rstrip()
            if self.__strip_right
            else self.__string_buffer.getvalue()
        )

    def write(self, *args, **kwargs):
        kwargs["file"] = self.__string_buffer
        print(*args, **kwargs)

    def title(self, message, character="=", up=True, down=False):
        if not isinstance(message, str):
            message = str(message)
        line = character * len(message)
        if up:
            self.write(line)
        self.write(message)
        if down:
            self.write(line)


class Table:
    __slots__ = ("headers", "lines")

    def __init__(self, headers, lines):
        # type: (List[str], List[List[Any]]) -> None
        self.headers = headers
        self.lines = lines

    def __str__(self):
        header_sizes = [
            max(
                len(str(self.headers[i])),
                max([len(str(line[i])) for line in self.lines if line] + [0]),
            )
            + 2
            for i in range(len(self.headers))
        ]
        with StringPrinter() as printer:
            printer.write(
                "".join(
                    str(self.headers[i]).ljust(header_sizes[i])
                    for i in range(len(self.headers))
                )
            )
            for line in self.lines:
                if line:
                    printer.write(
                        "".join(
                            str(line[i]).ljust(header_sizes[i])
                            for i in range(len(self.headers))
                        )
                    )
                else:
                    printer.write()
            return str(printer)

    def to_json(self):
        return [self.headers] + self.lines


class ToDict:
    __slots__ = ()
    __slot_sorter__ = sorted
    __print_none__ = False

    def get_name(self):
        return type(self).__name__

    @classmethod
    def get_slots(cls):
        if hasattr(cls, "__props__"):
            return cls.__props__
        return cls.__slot_sorter__(
            chain.from_iterable(getattr(typ, "__slots__", ()) for typ in cls.__mro__)
        )

    @classmethod
    def get_args_from(cls, dictionary: dict):
        return {field: dictionary[field] for field in cls.get_slots()}

    def to_dict(self, **extra):
        dct = {field: getattr(self, field) for field in self.get_slots()}
        dct.update(extra)
        return dct

    def __str__(self):
        values = []
        for name in self.get_slots():
            value = getattr(self, name)
            if self.__print_none__ or value is not None:
                values.append((name, value))
        return "%s(%s)" % (
            self.get_name(),
            ", ".join(
                "%s=%s" % (name, repr(value) if isinstance(value, str) else value)
                for name, value in values
            ),
        )

    def __eq__(self, other):
        return all(
            getattr(self, field) == getattr(other, field) for field in self.get_slots()
        )


class ToFulLDict(ToDict):
    __slots__ = ()
    __print_none__ = True


class Enumeration:
    __slots__ = "values", "type"

    def __init__(self, enum_values):
        self.values = set(enum_values)
        if len(self.values) < 2:
            raise ValueError(
                "Invalid enumeration: expected at least 2 values, got %s"
                % len(self.values)
            )
        types = {type(value) for value in self.values}
        if len(types) != 1:
            raise ValueError(
                "Invalid enumeration: expected exactly 1 type for all values, got %s"
                % len(types)
            )
        self.type = next(iter(types))
        if self.type not in (bool, int, float, str):
            raise ValueError(
                "Invalid enumeration: expected basic type for values, got %s"
                % self.type
            )

    def __call__(self, value):
        if value not in self.values:
            raise ValueError(
                "Invalid value\n\tGot: %s\n\tExpected:%s\n" % (value, self)
            )
        return value

    def __str__(self):
        return "{%s}" % (", ".join(sorted(self.values)))

    def __repr__(self):
        return str(self)


class Context:
    __slots__ = ["_context"]

    def __init__(self):
        self._context = False

    def __getattribute__(self, item):
        if not object.__getattribute__(self, "_context"):
            raise RuntimeError(f"{type(self).__name__} object not used as a context")
        return object.__getattribute__(self, item)

    @abstractmethod
    def on_exit(self):
        pass

    def __enter__(self):
        self._context = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ret = self.on_exit()
        self._context = False
        return ret


class ListView(Generic[T]):
    __slots__ = ("__seq", "__start", "__end")

    def __init__(self, sequence, start, end):
        # type: (List[T], int, int) -> None
        self.__seq = sequence
        self.__start = max(len(sequence) + start if start < 0 else start, 0)
        self.__end = min(
            max(len(sequence) + end if end < 0 else end, self.__start), len(sequence)
        )

    def __len__(self):
        return self.__end - self.__start

    def __bool__(self):
        return self.__end != self.__start

    def __getitem__(self, item):
        return self.__seq[self.__end + item if item < 0 else self.__start + item]

    def __iter__(self):
        return (self.__seq[i] for i in range(self.__start, self.__end))


class Text:
    __slots__ = ("value",)

    def __init__(self, value=""):
        self.value = value or ""

    def __bool__(self):
        return bool(self.value)

    def __str__(self):
        return self.value

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return self.value == other.value

    def __lt__(self, other):
        return (
            locale.strcoll(self.value.lower(), other.value.lower())
            or -locale.strcoll(self.value, other.value)
        ) < 0


class AbstractMatrix:
    __slots__ = ("width", "height")

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

    @abstractmethod
    def data(self):
        raise NotImplementedError()
