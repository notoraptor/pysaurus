from abc import abstractmethod
from io import StringIO
from itertools import chain
from typing import Any, Generic, List, TypeVar

from pysaurus.core.functions import to_printable, pgcd

T = TypeVar('T')


class StringPrinter(object):
    __slots__ = 'string_buffer', 'strip_right'

    def __init__(self, strip_right=True):
        self.string_buffer = StringIO()
        self.strip_right = bool(strip_right)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.string_buffer.close()

    def __str__(self):
        return self.string_buffer.getvalue().rstrip() if self.strip_right else self.string_buffer.getvalue()

    def write(self, *args, **kwargs):
        kwargs['file'] = self.string_buffer
        print(*args, **kwargs)

    def title(self, message, character='=', up=True, down=False):
        if not isinstance(message, str):
            message = str(message)
        line = character * len(message)
        if up:
            self.write(line)
        self.write(message)
        if down:
            self.write(line)


class Table:
    __slots__ = ('headers', 'lines')

    def __init__(self, headers, lines):
        # type: (List[str], List[List[Any]]) -> None
        self.headers = headers
        self.lines = lines

    def __str__(self):
        header_sizes = [max(len(str(self.headers[i])),
                            max([len(str(line[i])) for line in self.lines if line] + [0])) + 2
                        for i in range(len(self.headers))]
        with StringPrinter() as printer:
            printer.write(''.join(
                str(self.headers[i]).ljust(header_sizes[i]) for i in range(len(self.headers))))
            for line in self.lines:
                if line:
                    printer.write(''.join(
                        str(line[i]).ljust(header_sizes[i]) for i in range(len(self.headers))))
                else:
                    printer.write()
            return str(printer)

    def to_json(self):
        return [self.headers] + self.lines


class ToDict:
    __slots__ = ()

    def get_name(self):
        return type(self).__name__

    def get_slots(self):
        if hasattr(self, '__props__'):
            return self.__props__
        return sorted(
            chain.from_iterable(getattr(cls, '__slots__', ()) for cls in type(self).__mro__))

    def to_dict(self, **extra):
        dct = {field: getattr(self, field) for field in self.get_slots()}
        if extra:
            dct.update(extra)
        return dct

    def __str__(self):
        values = []
        for name in self.get_slots():
            value = getattr(self, name)
            if value is not None:
                values.append((name, value))
        return '%s(%s)' % (self.get_name(), ', '.join('%s=%s' % (name, to_printable(value)) for name, value in values))


class Enumeration:
    __slots__ = 'values',

    def __init__(self, enum_values):
        self.values = set(enum_values)

    def __call__(self, value):
        if value not in self.values:
            raise ValueError('Invalid value\n\tGot: %s\n\tExpected:%s\n' % (value, self))
        return value

    def __str__(self):
        return '{%s}' % (', '.join(sorted(self.values)))

    def __repr__(self):
        return str(self)


class Context:
    __slots__ = ['_context']

    def __init__(self):
        self._context = False

    def __getattribute__(self, item):
        if not object.__getattribute__(self, '_context'):
            raise RuntimeError('%s object not used as a context' % type(self).__name__)
        return object.__getattribute__(self, item)

    @abstractmethod
    def on_exit(self):
        pass

    def __enter__(self):
        self._context = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.on_exit()
        self._context = False


class ListView(Generic[T]):
    __slots__ = ('__seq', '__start', '__end')

    def __init__(self, sequence, start, end):
        # type: (List[T], int, int) -> None
        self.__seq = sequence
        self.__start = max(len(sequence) + start if start < 0 else start, 0)
        self.__end = min(max(len(sequence) + end if end < 0 else end, self.__start), len(sequence))

    def __len__(self):
        return self.__end - self.__start

    def __bool__(self):
        return self.__end != self.__start

    def __getitem__(self, item):
        return self.__seq[self.__end + item if item < 0 else self.__start + item]

    def __iter__(self):
        return (self.__seq[i] for i in range(self.__start, self.__end))


class Fraction:
    __slots__ = 'sign', 'num', 'den'

    def __init__(self, a, b):
        # type: (int, int) -> None
        if b == 0:
            raise ZeroDivisionError('%d/%d' % (a, b))
        if a == 0:
            self.sign = 1
            self.num = 0
            self.den = 1
            return
        if a < 0 and b < 0:
            self.sign = 1
            self.num = -a
            self.den = -b
        elif a * b < 0:
            self.sign = -1
            self.num = abs(a)
            self.den = abs(b)
        else:
            # a > 0 and b > 0
            self.sign = 1
            self.num = a
            self.den = b
        d = pgcd(self.num, self.den)
        self.num //= d
        self.den //= d

    def __float__(self):
        return self.sign * self.num / self.den

    def __str__(self):
        if self.den == 0:
            return '0'
        if self.den == 1:
            return '%s%d' % ('-' if self.sign < 0 else '', self.num)
        return '%s%d/%d' % ('-' if self.sign < 0 else '', self.num, self.den)

    def __hash__(self):
        return hash((self.sign, self.num, self.den))

    def __eq__(self, other):
        return self.sign == other.sign and self.num == other.num and self.den == other.den

    def __lt__(self, other):
        if self.sign == other.sign:
            return self.sign * (self.num * other.den - self.den * other.num) < 0
        return self.sign < other.sign
