from html.parser import HTMLParser
from io import StringIO

import whirlpool


class Enumeration:
    __slots__ = 'values',

    def __init__(self, values):
        self.values = set(values)

    def __call__(self, value):
        if value not in self.values:
            raise ValueError('Invalid value\n\tGot: %s\n\tExpected:%s\n' % (value, self.values))
        return value


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
