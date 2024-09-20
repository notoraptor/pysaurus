import bisect
import logging
import re
import sys
import tempfile
import threading
import types
from typing import Collection, Iterable, List, Sequence

logger = logging.getLogger(__name__)

REGEX_NO_WORD = re.compile(r"(\W|_)+")
REGEX_CONSECUTIVE_UPPER_CASES = re.compile("[A-Z]{2,}")
REGEX_LOWER_THEN_UPPER_CASES = re.compile("([a-z0-9])([A-Z])")
REGEX_WORD_THEN_NUMBER = re.compile(r"([^0-9 ])([0-9])")
REGEX_NUMBER_THEN_WORD = re.compile(r"([0-9])([^0-9 ])")
REGEX_NUMBER = re.compile(r"([0-9]+)")
REGEX_ATTRIBUTE = re.compile(r"^[a-z][a-zA-Z0-9_]*$")
JSON_INTEGER_MIN = -(2**31)
JSON_INTEGER_MAX = 2**31 - 1

DISCARDED_CHARACTERS = r"@#\\/?$:!"

__fn_types__ = (
    types.FunctionType,
    types.MethodType,
    types.BuiltinMethodType,
    types.BuiltinFunctionType,
    types.ClassMethodDescriptorType,
    classmethod,
    staticmethod,
    property,
)


def is_attribute_name(key):
    return REGEX_ATTRIBUTE.match(key)


def is_attribute_value(key, value):
    return REGEX_ATTRIBUTE.match(key) and not isinstance(value, __fn_types__)


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


def string_to_pieces(the_string) -> List[str]:
    the_string = camel_case_to_snake_case(the_string, split_upper_cases=False)
    the_string = split_words_and_numbers(the_string)
    return [piece.lower() for piece in REGEX_NO_WORD.sub(" ", the_string).split()]


def flat_to_coord(index, width):
    # i => (x, y)
    return index % width, index // width


def coord_to_flat(x, y, width):
    # (x, y) => i
    return y * width + x


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


def extract_object(instance: object, path: str):
    """Extract an attribute from instance using dot separated path.

    E.g. extract_object(my_object, "attr1.attr2.attr3")
    will return my_object.attr1.attr2.attr3
    """
    element = instance
    for step in path.split("."):
        element = getattr(element, step)
    return element


def generate_infinite(value):
    def gen():
        while True:
            yield value

    return gen()


def remove_from_list(arr: List, el):
    try:
        return arr.remove(el)
    except ValueError:
        pass


def generate_temporary_file(basename="pysaurus", suffix=".pkl"):
    """Generate a temporary file where data could be saved.
    Create an empty file without collision.
    Return name of generated file.
    """
    with tempfile.NamedTemporaryFile(
        prefix=f"{basename}_", suffix=suffix, delete=False
    ) as tf:
        return tf.name


def make_collection(something) -> Collection:
    return something if isinstance(something, (list, tuple, set)) else [something]


def ensure_list_or_tuple(data):
    if isinstance(data, set):
        data = list(data)
    elif not isinstance(data, (list, tuple)):
        data = [data]
    return data


def expand_if(expression) -> Sequence:
    """
    Return expression as a sequence, intended to be used with splat operator.
    If expression is evaluated to False, then an empty list is returned.

    Examples:
        my_list = [a, b, *expand_if_not_false(d if c else None)]
        # Will produce same list as above:
        my_list = [a, b, *expand_if_not_false(c and d)]

    :param expression: object to expand
    :return: a sequence (list or tuple)
    """
    if not expression:
        return []
    elif isinstance(expression, (list, tuple)):
        return expression
    else:
        return [expression]


def are_hashable_by(elements: Sequence, attribute: str) -> bool:
    return len({getattr(el, attribute) for el in elements}) == len(elements)
