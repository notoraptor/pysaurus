"""Functions moved from pysaurus.core.functions (unused in the codebase)."""

import bisect
import inspect
import re
import types
from collections.abc import Callable
from typing import Any, Collection, Sequence

REGEX_NUMBER = re.compile(r"([0-9]+)")
REGEX_ATTRIBUTE = re.compile(r"^[a-z][a-zA-Z0-9_]*$")
JSON_INTEGER_MIN = -(2**31)
JSON_INTEGER_MAX = 2**31 - 1

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


def separate_text_and_numbers(text: str):
    pieces = REGEX_NUMBER.split(text)
    for i in range(1, len(pieces), 2):
        pieces[i] = int(pieces[i])
    return tuple(pieces)


def flat_to_coord(index, width):
    # i => (x, y)
    return index % width, index // width


def coord_to_flat(x, y, width):
    # (x, y) => i
    return y * width + x


get_start_index = bisect.bisect_left
get_end_index = bisect.bisect_right


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
    """Compare elements and deeply compare lists, tuples and dict values."""
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


def compute_nb_couples(n: int):
    return (n * (n - 1)) // 2 if n > 1 else 0


def indent_string_tree(tree: list, indent="", indentation="\t"):
    return "\n".join(
        (
            indent_string_tree(entry, indent + indentation, indentation=indentation)
            if isinstance(entry, list)
            else f"{indent}{entry}"
        )
        for entry in tree
    )


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


def remove_from_list(arr: list, el):
    try:
        return arr.remove(el)
    except ValueError:
        pass


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


def map_attribute[T](elements: Sequence[T], attribute: str) -> dict[Any, T]:
    mapping = {getattr(element, attribute): element for element in elements}
    assert len(mapping) == len(elements)
    return mapping


def boolean_and(a, b):
    return a and b


def boolean_or(a, b):
    return a or b


def if_else(x, y, z):
    return y if x else z


def get_percent(a, b, decimals=2):
    return round(a * 100 / b, decimals)


def get_tagged_methods(obj, key: str) -> dict[Any, Callable]:
    """
    Collect methods from given object which have an attribute named `key`
    :param obj: object to inspect
    :param key: attribute to lookup in object
    :return: a dictionary mapping key value to method
        for each matching method in given object.
    """
    tag_to_method = {}
    for name, method in inspect.getmembers(obj, inspect.ismethod):
        if hasattr(method, key):
            value = getattr(method, key)
            assert value not in tag_to_method
            tag_to_method[value] = method
    return tag_to_method


def points_are_line(points: list[tuple[int, int]]) -> bool:
    """
    Check if the points are a line or a polygon.

    Generated with Jetbrains AI Assistant.
    """
    if len(points) < 2:
        return False
    if len(points) == 2:
        return True
    # Check if all points are collinear
    x0, y0 = points[0]
    x1, y1 = points[1]
    dx = x1 - x0
    dy = y1 - y0
    for x, y in points[2:]:
        if (y - y0) * dx != (x - x0) * dy:
            return False
    return True
