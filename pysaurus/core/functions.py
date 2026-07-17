import logging
import re
import tempfile
import threading

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


def compute_nb_pages(count, page_size):
    return (count // page_size) + bool(count % page_size)


def get_default(value, default):
    return default if value is None else value


def generate_temporary_file(basename="pysaurus", suffix=".pkl"):
    """Generate a temporary file where data could be saved.
    Create an empty file without collision.
    Return name of generated file.
    """
    with tempfile.NamedTemporaryFile(
        prefix=f"{basename}_", suffix=suffix, delete=False
    ) as tf:
        return tf.name
