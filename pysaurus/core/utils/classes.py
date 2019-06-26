import sys
from html.parser import HTMLParser
from io import StringIO
from itertools import chain
from typing import List, Any

import whirlpool

from pysaurus.core.utils.functions import to_printable


class StringPrinter(object):
    __slots__ = 'string_buffer', 'strip_right'

    def __init__(self, strip_right=True):
        self.string_buffer = StringIO()
        self.strip_right = bool(strip_right)

    def __del__(self):
        if not self.string_buffer.closed:
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


class Whirlpool:
    wp = None

    @staticmethod
    def hash(string: str):
        if not Whirlpool.wp:
            Whirlpool.wp = whirlpool.new()
        Whirlpool.wp.update(string.encode())
        return Whirlpool.wp.hexdigest().lower()


class HTMLStripper(HTMLParser):
    """ HTML parser class to remove HTML tags from a string.
        Example:
            text = HTMLStripper.strip(text)
        Reference: (2018/09/24) https://stackoverflow.com/a/925630
    """

    def __init__(self):
        """ Constructor """
        super(HTMLStripper, self).__init__(convert_charrefs=True)
        self.fed = []

    def handle_data(self, data):
        """ Split text to blank delimiters and store text pieces. """
        self.fed.extend(data.split())

    def get_data(self):
        """ Return filtered text pieces, joined with space.
            Each spaces sequence should contain only 1 space in returned text.
        """
        return ' '.join(self.fed)

    @classmethod
    def strip(cls, msg):
        """ Remove HTML tags from given message and return stripped message. """
        html_stripper = HTMLStripper()
        html_stripper.feed(msg)
        return html_stripper.get_data()


class Table:
    __slots__ = ('headers', 'lines')

    def __init__(self, headers, lines):
        # type: (List[str], List[List[Any]]) -> None
        self.headers = headers
        self.lines = lines

    def __str__(self):
        printer = StringPrinter()
        header_sizes = [max(len(str(self.headers[i])), max(len(str(line[i])) for line in self.lines if line)) + 2
                        for i in range(len(self.headers))]
        printer.write(''.join(str(self.headers[i]).ljust(header_sizes[i]) for i in range(len(self.headers))))
        for line in self.lines:
            if line:
                printer.write(''.join(str(line[i]).ljust(header_sizes[i]) for i in range(len(self.headers))))
            else:
                printer.write()
        return str(printer)

    def to_json(self):
        return [self.headers] + self.lines


class ToDict:
    __slots__ = []

    def get_name(self):
        return type(self).__name__

    def get_slots(self):
        return chain.from_iterable(getattr(cls, '__slots__', []) for cls in type(self).__mro__)

    def to_dict(self, **extra):
        dct = {field: getattr(self, field) for field in self.get_slots()}
        if extra:
            dct.update(extra)
        return dct

    def __str__(self):
        return '%s(%s)' % (
            self.get_name(),
            ', '.join('%s=%s' % (name, to_printable(getattr(self, name))) for name in sorted(self.__slots__)))


class System:
    @staticmethod
    def is_windows():
        return sys.platform == 'win32'

    @staticmethod
    def is_linux():
        return sys.platform == 'linux'

    @staticmethod
    def is_mac():
        return sys.platform == 'darwin'
