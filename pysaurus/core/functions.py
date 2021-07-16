import bisect
import concurrent.futures
import math
import os
import re
import tempfile
import threading
import urllib.parse
from datetime import datetime

from pysaurus.core.constants import VIDEO_SUPPORTED_EXTENSIONS
from pysaurus.core.modules import HTMLStripper

# Datetime since timestamp 0.
EPOCH = datetime.utcfromtimestamp(0)
REGEX_NO_WORD = re.compile(r"(\W|_)+")
REGEX_CONSECUTIVE_UPPER_CASES = re.compile("[A-Z]{2,}")
REGEX_LOWER_THEN_UPPER_CASES = re.compile("([a-z0-9])([A-Z])")
REGEX_WORD_THEN_NUMBER = re.compile(r"([^0-9 ])([0-9])")
REGEX_NUMBER_THEN_WORD = re.compile(r"([0-9])([^0-9 ])")
REGEX_NUMBER = re.compile(r"([0-9]+)")
JSON_INTEGER_MIN = -(2 ** 31)
JSON_INTEGER_MAX = 2 ** 31 - 1


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
    :param split_upper_cases: if True, split consecutives uppercases too (e.g. 'ABC' => 'a_b_c')
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


def is_valid_video_filename(filename):
    _, extension = os.path.splitext(filename)
    return extension and extension[1:].lower() in VIDEO_SUPPORTED_EXTENSIONS


def dispatch_tasks(tasks, job_count, extra_args=None):
    # type: (list, int, list) -> list
    """Split <tasks> into <job_count> jobs and associate each one
    with an unique job ID starting from <next_job_id>, so that
    each job could assign an unique ID to each of his task by
    incrementing his job ID when managing his tasks.
    :param tasks: a list of tasks to split.
    :param job_count: number of jobs.
    :param extra_args: (optional) list
    :return: a list of lists each containing (job, job ID, and extra args if provided).
    """
    if extra_args is None:
        extra_args = []
    task_count = len(tasks)
    if job_count > task_count:
        job_lengths = [1] * task_count
    else:
        job_lengths = [task_count // job_count] * job_count
        for i in range(task_count % job_count):
            job_lengths[i] += 1
    if sum(job_lengths) != task_count:
        raise ValueError(
            "Programming error when dispatching tasks: total expected %d, got %d."
            % (task_count, sum(job_lengths))
        )
    cursor = 0
    jobs = []
    job_id = 0
    job_count = len(job_lengths)
    for job_len in job_lengths:
        job_id += 1
        jobs.append(
            [tasks[cursor : (cursor + job_len)], "%d/%d" % (job_id, job_count)]
            + extra_args
        )
        cursor += job_len
    # NB: next_job_id is now next_job_id + len(tasks).
    return jobs


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


def package_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def bool_type(mixed):
    """Convert a value to a boolean, with following rules (in that order):
        None => False
        bool, int, float => False if 0, else True
        "true" (case insensitive) => True
        "false" (case insensitive) => False
        "" (empty string) => False
        integer or floating string => boolean value of converted number (False if 0, else True)
        bool(mixed) otherwise.
    :param mixed:
    :return:
    """
    if mixed is None:
        return False
    if isinstance(mixed, (bool, int, float)):
        return bool(mixed)
    if isinstance(mixed, str):
        if mixed.lower() == "true":
            return True
        if not mixed or mixed.lower() == "false":
            return False
        try:
            return bool(int(mixed))
        except ValueError:
            try:
                return bool(float(mixed))
            except ValueError:
                pass
    return bool(mixed)


def timestamp_microseconds():
    """Return current timestamp with microsecond resolution.
    :return: int
    """
    delta = datetime.now() - EPOCH
    return (delta.days * 24 * 60 * 60 + delta.seconds) * 1000000 + delta.microseconds


def flat_to_coord(index, width):
    # i => (x, y)
    return index % width, index // width


def coord_to_flat(x, y, width):
    # (x, y) => i
    return y * width + x


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


def get_file_extension(string):
    # type: (str) -> str
    index_of_dot = string.rfind(".")
    if index_of_dot >= 0:
        return string[(index_of_dot + 1) :].lower()
    return ""


def get_plural_suffix(count, suffix="s"):
    return "" if count == 1 else suffix


def _pgcd(a, b):
    # type: (int, int) -> int
    return a if not b else _pgcd(b, a % b)


def pgcd(a, b):
    # type: (int, int) -> int
    """ "Plus grand commun diviseur" (Greatest Common Divider)"""
    if a < 0:
        a = -a
    if b < 0:
        b = -b
    if a < b:
        a, b = b, a
    return _pgcd(a, b)


def parallelize(function, jobs, cpu_count):
    with concurrent.futures.ProcessPoolExecutor(max_workers=cpu_count) as executor:
        results = list(executor.map(function, jobs))
    return results


def launch_thread(function, *args, **kwargs):
    thread = threading.Thread(target=function, args=args, kwargs=kwargs)
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


def identity(value):
    return value


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


get_start_index = bisect.bisect_left
get_end_index = bisect.bisect_right


def flatten_list(data: list):
    output = []
    for element in data:
        if isinstance(element, list):
            output.extend(flatten_list(element))
        else:
            output.append(element)
    return output


def class_get_public_attributes(cls: type, exclude=()):
    fields = {
        field
        for field in dir(cls)
        if "a" <= field[0] <= "z" and not callable(getattr(cls, field))
    }
    fields.difference_update(exclude)
    fields.difference_update(getattr(cls, "__protected__", ()))
    return sorted(fields)


def compute_nb_pages(count, page_size):
    return (count // page_size) + bool(count % page_size)


def to_printable(element):
    return repr(element) if isinstance(element, str) else element


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
