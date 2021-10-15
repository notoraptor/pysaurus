import locale
from abc import abstractmethod
from io import StringIO
from itertools import chain


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


class ToDict:
    __slots__ = ()
    __props__ = None
    __slot_sorter__ = sorted
    __print_none__ = False

    @classmethod
    def get_slots(cls):
        if cls.__props__ is not None:
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
        return "{}({})".format(
            type(self).__name__,
            ", ".join(
                f"{name}={repr(value) if isinstance(value, str) else value}"
                for name, value in values
            ),
        )

    def __eq__(self, other):
        return type(self) is type(other) and all(
            getattr(self, field) == getattr(other, field) for field in self.get_slots()
        )


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


class TextWithNumbers(Text):
    __slots__ = ("comparable",)

    def __init__(self, value=""):
        super().__init__(value)
        from pysaurus.core.functions import separate_text_and_numbers

        self.comparable = separate_text_and_numbers(self.value)

    def __lt__(self, other):
        return self.comparable < other.comparable


class AbstractMatrix:
    __slots__ = "width", "height"

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

    @abstractmethod
    def data(self):
        raise NotImplementedError()
