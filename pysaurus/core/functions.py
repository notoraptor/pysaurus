import logging
import re
import sys
import tempfile
import threading
from typing import Iterable

logger = logging.getLogger(__name__)

REGEX_NO_WORD = re.compile(r"(\W|_)+")
REGEX_CONSECUTIVE_UPPER_CASES = re.compile("[A-Z]{2,}")
REGEX_LOWER_THEN_UPPER_CASES = re.compile("([a-z0-9])([A-Z])")
REGEX_WORD_THEN_NUMBER = re.compile(r"([^0-9 ])([0-9])")
REGEX_NUMBER_THEN_WORD = re.compile(r"([0-9])([^0-9 ])")

DISCARDED_CHARACTERS = r"@#\\/?$:!"


def has_discarded_characters(txt: str):
    return any(c in txt for c in DISCARDED_CHARACTERS)


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


def split_words_and_numbers(text):
    text = REGEX_WORD_THEN_NUMBER.sub(r"\1 \2", text)
    text = REGEX_NUMBER_THEN_WORD.sub(r"\1 \2", text)
    return text


def string_to_pieces(the_string) -> list[str]:
    the_string = camel_case_to_snake_case(the_string, split_upper_cases=False)
    the_string = split_words_and_numbers(the_string)
    return [piece.lower() for piece in REGEX_NO_WORD.sub(" ", the_string).split()]


def _pgcd(a: int, b: int) -> int:
    return a if not b else _pgcd(b, a % b)


def pgcd(a: int, b: int) -> int:
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


def identity(value):
    return value


def do_nothing(*args, **kwargs):
    pass


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


def get_default(value, default):
    return default if value is None else value


def fatal(exception: Exception, code=1):
    print(f"{type(exception).__name__}:", exception, file=sys.stderr)
    exit(code)


def object_to_dict(obj, value_wrapper=identity):
    cls = obj if isinstance(obj, type) else type(obj)
    return {
        key: value_wrapper(getattr(obj, key))
        for key in class_get_public_attributes(cls)
    }


def apply_selector(selector: dict, data: Iterable, key: str, return_data=False):
    """Filter data using given selector.

    `selector` is a dictionary defining how to select data.

    It must contain a boolean key 'all' telling to take all data or not.
    - If 'all' is True, then a list key 'exclude' must be specified
      to list data to exclude.
      - 'exclude' can be an empty list to exclude nothing.
        Then all data will be selected.
    - If 'all' is False, then a list key 'include' must be specified
      to list data to include.
      - 'include' can be an empty list to include nothing.
        Then no data will be selected.

    'include' and 'exclude' must list attribute values to be taken in data objects
    to select them. The name of attribute to check is specified in `key` parameter.

    `data` is the iterable of data to filter.

    If `return_data` is True, then filtered data will be returned.
    Otherwise, data attribute values will be returned.
    """
    if selector["all"]:
        exclude = set(selector["exclude"])
        output = [
            (element if return_data else getattr(element, key))
            for element in data
            if getattr(element, key) not in exclude
        ]
    else:
        include = set(selector["include"])
        output = (
            [element for element in data if getattr(element, key) in include]
            if return_data
            else include
        )
    return output


def apply_selector_to_data(selector: dict, data: Iterable) -> list:
    if selector["all"]:
        exclude = set(selector["exclude"])
        output = [element for element in data if element not in exclude]
    else:
        output = selector["include"]
    return output


def generate_temporary_file(basename="pysaurus", suffix=".pkl"):
    """Generate a temporary file where data could be saved.
    Create an empty file without collision.
    Return name of generated file.
    """
    with tempfile.NamedTemporaryFile(
        prefix=f"{basename}_", suffix=suffix, delete=False
    ) as tf:
        return tf.name
