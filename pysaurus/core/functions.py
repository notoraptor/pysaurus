import bisect
import re
import sys
import threading

from pysaurus.core.modules import HTMLStripper

# Datetime since timestamp 0.
REGEX_NO_WORD = re.compile(r"(\W|_)+")
REGEX_CONSECUTIVE_UPPER_CASES = re.compile("[A-Z]{2,}")
REGEX_LOWER_THEN_UPPER_CASES = re.compile("([a-z0-9])([A-Z])")
REGEX_WORD_THEN_NUMBER = re.compile(r"([^0-9 ])([0-9])")
REGEX_NUMBER_THEN_WORD = re.compile(r"([0-9])([^0-9 ])")
REGEX_NUMBER = re.compile(r"([0-9]+)")
REGEX_ATTRIBUTE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")
JSON_INTEGER_MIN = -(2 ** 31)
JSON_INTEGER_MAX = 2 ** 31 - 1

DISCARDED_CHARACTERS = r"@#\\/?$:!"


def is_valid_attribute_name(key):
    return REGEX_ATTRIBUTE.match(key)


def has_discarded_characters(txt: str):
    return any(c in txt for c in DISCARDED_CHARACTERS)


def separate_text_and_numbers(text: str):
    pieces = REGEX_NUMBER.split(text)
    for i in range(1, len(pieces), 2):
        pieces[i] = int(pieces[i])
    return tuple(pieces)


def split_words_and_numbers(text):
    text = REGEX_WORD_THEN_NUMBER.sub(r"\1 \2", text)
    text = REGEX_NUMBER_THEN_WORD.sub(r"\1 \2", text)
    return text


def camel_case_to_snake_case(name, split_upper_cases=True):
    """Convert a string (expected to be in camel case) to snake case.
    :param name: string to convert.
    :param split_upper_cases: if True, also split consecutive uppercase letters
        (e.g. 'ABC' => 'a_b_c')
    :return: snake case version of given name.
    :rtype: str
    """
    if name == "":
        return name
    if split_upper_cases:
        name = REGEX_CONSECUTIVE_UPPER_CASES.sub(
            lambda m: "_".join(c for c in m.group(0)), name
        )
    return REGEX_LOWER_THEN_UPPER_CASES.sub(r"\1_\2", name).lower()


def string_to_pieces(the_string, as_set=False):
    builder = set if as_set else list
    the_string = camel_case_to_snake_case(the_string, split_upper_cases=False)
    the_string = split_words_and_numbers(the_string)
    return builder(
        piece.lower() for piece in REGEX_NO_WORD.sub(" ", the_string).split()
    )


def flat_to_coord(index, width):
    # i => (x, y)
    return index % width, index // width


def coord_to_flat(x, y, width):
    # (x, y) => i
    return y * width + x


def _pgcd(a, b):
    # type: (int, int) -> int
    return a if not b else _pgcd(b, a % b)


def pgcd(a, b):
    # type: (int, int) -> int
    """'Plus grand commun diviseur' (Greatest Common Divider)"""
    if a < 0:
        a = -a
    if b < 0:
        b = -b
    if a < b:
        a, b = b, a
    return _pgcd(a, b)


def launch_thread(function, *args, **kwargs):
    thread = threading.Thread(
        target=function, args=args, kwargs=kwargs, name=function.__name__
    )
    thread.start()
    return thread


def html_to_title(title):
    # type: (str) -> str
    """
    Remove HTML tags, simple and double starting/ending quotes from given string.
    :param title: text to clear
    :return: cleared text
    """
    if title:
        title = HTMLStripper.strip(title)
        strip_again = True
        while strip_again:
            strip_again = False
            for character in ('"', "'"):
                if title.startswith(character) and title.endswith(character):
                    title = title.strip(character)
                    strip_again = True
    return title


def identity(value):
    return value


def function_none(*args, **kwargs):
    return None


get_start_index = bisect.bisect_left
get_end_index = bisect.bisect_right


def class_get_public_attributes(cls: type, exclude=(), wrapper=sorted):
    fields = {
        field
        for field in dir(cls)
        if "a" <= field[0] <= "z" and not callable(getattr(cls, field))
    }
    fields.difference_update(exclude)
    fields.difference_update(getattr(cls, "__protected__", ()))
    return fields if wrapper is set else wrapper(fields)


def compute_nb_pages(count, page_size):
    return (count // page_size) + bool(count % page_size)


def to_json_value(value):
    if isinstance(value, (tuple, list, set)):
        return [to_json_value(element) for element in value]
    if isinstance(value, dict):
        return {
            to_json_value(key): to_json_value(element) for key, element in value.items()
        }
    if isinstance(value, (str, float, bool, type(None))):
        return value
    if isinstance(value, int) and JSON_INTEGER_MIN <= value <= JSON_INTEGER_MAX:
        return value
    return str(value)


def deep_equals(value, other):
    """Compare elements and deeply compare lists,, tuples and dict values."""
    value_type = type(value)
    assert value_type is type(other), (value_type, type(other))
    if value_type in (list, tuple):
        return len(value) == len(other) and all(
            deep_equals(value[i], other[i]) for i in range(len(value))
        )
    if value_type is set:
        return len(value) == len(other) and all(element in other for element in value)
    if value_type is dict:
        return len(value) == len(other) and all(
            key in other and deep_equals(value[key], other[key]) for key in value
        )
    return value == other


def get_default(value, default):
    return default if value is None else value


def compute_nb_couples(n: int):
    return (n * (n - 1)) // 2 if n > 1 else 0


def fatal(exception: Exception, code=1):
    print(f"{type(exception).__name__}:", exception, file=sys.stderr)
    exit(code)


def object_to_dict(obj, value_wrapper=identity):
    cls = obj if isinstance(obj, type) else type(obj)
    return {
        key: value_wrapper(getattr(obj, key))
        for key in class_get_public_attributes(cls)
    }


def indent_string_tree(tree: list, indent="", indentation="\t"):
    return "\n".join(
        (
            indent_string_tree(entry, indent + indentation, indentation=indentation)
            if isinstance(entry, list)
            else f"{indent}{entry}"
        )
        for entry in tree
    )


def unpack_args(function):
    """
    Wraps a function with multiple args into a function with a tuple as args.

    Decorator to wrap a function that receives multiple arguments f(*args)
    into a function that receives only a sequence of arguments g(args)
    """

    def wrapper(args):
        return function(*args)

    wrapper.__name__ = function.__name__

    return wrapper
