import bisect
import math
import os
import tempfile
import urllib.parse
from datetime import datetime

from pysaurus.core.components import AbsolutePath

EPOCH = datetime.utcfromtimestamp(0)


def permute(values, initial_permutation=()):
    """Generate a sequence of permutations from given values list."""
    initial_permutation = list(initial_permutation)
    if not values:
        yield initial_permutation
        return
    for position in range(len(values)):
        extended_permutation = initial_permutation + [values[position]]
        remaining_values = values[:position] + values[(position + 1) :]
        for permutation in permute(remaining_values, extended_permutation):
            yield permutation


def bool_type(mixed):
    """Convert a value to a boolean, with following rules (in that order):
    - "true" (case insensitive) => True
    - "false" (case insensitive) => False
    - "" (empty string) => False
    - integer or floating string => boolean value of converted number
    - bool(mixed) otherwise.
    """
    if isinstance(mixed, str):
        mixed = mixed.strip()
        if not mixed:
            return False
        elif mixed.lower() == "true":
            return True
        elif mixed.lower() == "false":
            return False
        else:
            return bool(float(mixed))
    return bool(mixed)


def timestamp_microseconds():
    """Return current timestamp with microsecond resolution.
    :return: int
    """
    delta = datetime.now() - EPOCH
    return (delta.days * 24 * 60 * 60 + delta.seconds) * 1000000 + delta.microseconds


def coordinates_around(x, y, width, height, radius=1):
    coordinates = []
    for local_x in range(max(0, x - radius), min(x + radius, width - 1) + 1):
        for local_y in range(max(0, y - radius), min(y + radius, height - 1) + 1):
            coordinates.append((local_x, local_y))
    return coordinates


def get_vector_angle(a, b):
    """Return the angle of vector a->b wrt/ horizontal vector (x = 1, y = 0).
    a and b must be each a couple of coordinates (x, y).
    """
    if a == b:
        return 0
    x_a, y_a = a
    x_b, y_b = b
    sin_theta = (y_b - y_a) / math.sqrt((x_b - x_a) ** 2 + (y_b - y_a) ** 2)
    deg = 180 * math.asin(sin_theta) / math.pi
    if (x_b - x_a) < 0:
        deg = 180 - deg
    elif sin_theta < 0:
        deg = 360 + deg
    return deg


def get_plural_suffix(count, suffix="s"):
    return "" if count == 1 else suffix


def assert_data_is_serializable(data, path=()):
    if isinstance(data, list):
        for index, element in enumerate(data):
            assert_data_is_serializable(element, path + (index,))
    elif isinstance(data, dict):
        for key, value in data.items():
            current_path = path + (key,)
            assert isinstance(key, str), current_path
            assert_data_is_serializable(value, current_path)
    else:
        assert isinstance(data, (bool, int, float, str)), (path, data)


def __get_start_index(sorted_content: list, element):
    # a[i:] >= x
    return bisect.bisect_left(sorted_content, element)
    # position = bisect.bisect_left(sorted_content, element)
    # if position != len(sorted_content):
    #     return position
    # return None


def __get_end_index(sorted_content: list, element):
    # a[i:] > x
    return bisect.bisect_right(sorted_content, element)


def flatten_list(data: list):
    output = []
    for element in data:
        if isinstance(element, list):
            output.extend(flatten_list(element))
        else:
            output.append(element)
    return output


def class_get_field_title(cls: type, field: str, lowercase=False):
    title = getattr(cls, "__titles__", {}).get(field, None)
    if not title:
        pieces = field.split("_")
        if not lowercase:
            pieces[0] = pieces[0].title()
        return " ".join(pieces)
    return title


def convert_file_path_to_url(path):
    entry_path = os.path.normpath(path).replace("\\", "/")
    return f"file:///{entry_path}"


def html_to_url(html):
    url = f"data:text/html;charset=UTF-8,{urllib.parse.quote(html)}"
    if len(url) < 2 * 1024 * 1024:
        return url
    # Url is too long, we should better save it in a file.
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as tf:
        tf.write(html)
        return convert_file_path_to_url(tf.name)


def min_and_max(values):
    iterable_values = iter(values)
    min_value = max_value = next(iterable_values)
    for value in iterable_values:
        min_value = min(min_value, value)
        max_value = max(max_value, value)
    return min_value, max_value


def assert_str(value):
    assert isinstance(value, str)
    return value


def is_instance_from_module(module, obj):
    typ = obj if isinstance(obj, type) else type(obj)
    return any(cls.__module__ == module.__name__ for cls in typ.__mro__)


def generate_non_existing_path(directory, name, extension):
    file_id = 0
    while True:
        file_path = AbsolutePath.file_path(directory, f"{name}{file_id}", extension)
        if file_path.exists():
            file_id += 1
        else:
            break
    return file_path


def to_printable(element):
    return repr(element) if isinstance(element, str) else element


def is_sequence(seq_to_check):
    """Check if given variable is a sequence-like object.
    Note that strings and dictionary-like objects will not be considered as sequences.

    :param seq_to_check: Sequence-like object to check.
    :return: Indicates if the object is sequence-like.
    :rtype: bool
    """
    # Strings and dicts are not valid sequences.
    if isinstance(seq_to_check, str) or is_dictionary(seq_to_check):
        return False
    return hasattr(seq_to_check, "__iter__")


def is_dictionary(dict_to_check):
    """Check if given variable is a dictionary-like object.

    :param dict_to_check: Dictionary to check.
    :return: Indicates if the object is a dictionary.
    :rtype: bool
    """
    return isinstance(dict_to_check, dict) or all(
        hasattr(dict_to_check, expected_attribute)
        for expected_attribute in (
            "__len__",
            "__contains__",
            "__bool__",
            "__iter__",
            "__getitem__",
            "keys",
            "values",
            "items",
        )
    )


def get_file_extension(string):
    # type: (str) -> str
    index_of_dot = string.rfind(".")
    if index_of_dot >= 0:
        return string[(index_of_dot + 1) :].lower()
    return ""
