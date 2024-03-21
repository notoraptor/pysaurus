import functools
import locale
from abc import abstractmethod
from io import StringIO
from itertools import chain
from typing import Iterable


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

    __repr__ = __str__

    def __eq__(self, other):
        return type(self) is type(other) and all(
            getattr(self, field) == getattr(other, field) for field in self.get_slots()
        )


class Text:
    """Helper class to compare texts.

    Compare case-insensitive then put lowercase first.
    """

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
        # Compare case-insensitive then with lowercase < uppercase>.
        return (
            locale.strcoll(self.value.lower(), other.value.lower())
            or -locale.strcoll(self.value, other.value)
        ) < 0


class AbstractMatrix:
    __slots__ = "width", "height"

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

    @abstractmethod
    def data(self):
        raise NotImplementedError()


class StringedTuple(tuple):
    """A tuple that prints elements with str instead of repr"""

    def __str__(self):
        return f"({', '.join(str(arg) for arg in self)})"


class Runnable:
    """Helper class to make a method automatically run in a separate process

    Target class must provide a launcher method
    to be used to run a function asynchronously.

    Runnable instance can then be used as a decorator on other class methods.

    Example:
        runnable = Runnable("my_launcher_method")

        class MyClass:
            def my_launcher_method(fn, args, my_arg1=None, my_arg2=None):
                pass

            @runnable()
            def a_task():
                pass

            @runnable(my_arg2="an arg for launcher method")
            def another_task():
                pass
    """

    __slots__ = ("__lmm",)

    def __init__(self, launcher_method_name: str):
        """Initialize runnable.

        :param launcher_method_name: name of method to be used to run functions
            asynchronously.
        """
        self.__lmm = launcher_method_name

    def __call__(self_, **kwargs):
        launcher_method_name = self_.__lmm

        def decorator(fn):
            @functools.wraps(fn)
            def wrapper(self, *args):
                getattr(self, launcher_method_name)(fn, (self,) + args, **kwargs)

            return wrapper

        return decorator


class Selector:
    __slots__ = ("to_exclude", "selection")

    def __init__(self, exclude: bool, selection: set):
        self.to_exclude = exclude
        self.selection = selection

    def filter(self, data: Iterable) -> list:
        if self.to_exclude:
            return [element for element in data if element not in self.selection]
        else:
            return [element for element in data if element in self.selection]

    def to_sql(self, field: str):
        selection = list(self.selection)
        placeholders = ",".join(["?"] * len(selection))
        if self.to_exclude:
            query = f"{field} NOT IN ({placeholders})"
        else:
            query = f"{field} IN ({placeholders})"
        return query, selection

    @classmethod
    def parse_dict(cls, selector: dict):
        if selector["all"]:
            to_exclude = True
            selection = set(selector["exclude"])
        else:
            to_exclude = False
            selection = set(selector["include"])
        return cls(to_exclude, selection)
