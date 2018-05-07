import os
import re
import sys
import whirlpool
from datetime import datetime
from io import StringIO

PACKAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))

# Regex used for conversion from camel case to snake case.
REGEX_CONSECUTIVE_UPPER_CASES = re.compile('[A-Z]{2,}')
REGEX_LOWER_THEN_UPPER_CASES = re.compile('([a-z0-9])([A-Z])')
REGEX_UNDERSCORE_THEN_LETTER = re.compile('_([a-z])')
REGEX_START_BY_LOWERCASE = re.compile('^[a-z]')


def __load_extensions():
    """ Load video supported extensions from `PACKAGE_DIR/pysaurus/extensions.txt` in a frozen set. """
    extensions = []
    extension_filename = os.path.join(PACKAGE_DIR, 'pysaurus', 'utils', 'extensions.txt')
    with open(extension_filename, 'r') as extension_file:
        for line in extension_file.readlines():
            line = line.strip()
            if line and not line.startswith('#'):
                extensions.append(line.lower())
    return frozenset(extensions)


VIDEO_SUPPORTED_EXTENSIONS = __load_extensions()


def string_print(*args, **kwargs):
    string_buffer = StringIO()
    kwargs['file'] = string_buffer
    print(*args, **kwargs)
    string_version = string_buffer.getvalue()
    string_buffer.close()
    return string_version


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

    def title(self, message, character='='):
        line = character * len(message)
        self.write(line)
        self.write(message)
        self.write(line)
        return len(message)


def timestamp_microseconds():
    """ Return current timestamp with microsecond resolution. """
    current_time = datetime.now()
    epoch = datetime.utcfromtimestamp(0)
    delta = current_time - epoch
    return (delta.days * 24 * 60 * 60 + delta.seconds) * 1000000 + delta.microseconds


def camel_case_to_snake_case(name):
    """ Convert a string (expected to be in camel case) to snake case.
        :param name: string to convert.
        :return: string: snake case version of given name.
    """
    if name == '':
        return name
    separated_consecutive_uppers = REGEX_CONSECUTIVE_UPPER_CASES.sub(lambda m: '_'.join(c for c in m.group(0)), name)
    return REGEX_LOWER_THEN_UPPER_CASES.sub(r'\1_\2', separated_consecutive_uppers).lower()


def snake_case_to_upper_camel_case(name):
    """ Convert a string (expected to be in snake case) to camel case and convert first letter to upper case
        if it's in lowercase.
        :param name: string to convert.
        :return: camel case version of given name.
    """
    if name == '':
        return name
    first_lower_case_to_upper = REGEX_START_BY_LOWERCASE.sub(lambda m: m.group(0).upper(), name)
    return REGEX_UNDERSCORE_THEN_LETTER.sub(lambda m: m.group(1).upper(), first_lower_case_to_upper)


def is_sequence(variable):
    return hasattr(variable, '__iter__')


def is_valid_video_filename(filename):
    _, extension = os.path.splitext(filename)
    return extension and extension[1:].lower() in VIDEO_SUPPORTED_EXTENSIONS


def has_extension(filename: str, extension: str):
    return len(filename) >= len(extension) + 1 and filename.endswith(extension) and filename[-len(extension) - 1] == '.'


def hash_with_whirlpool(string: str):
    wp = whirlpool.new(string.encode())
    return wp.hexdigest().upper()


def default(dct, key, fn):
    """ Return dct[key] if key in dct, else value returned by fn().
    :param dct: a dictionary-like object
    :param key: a key to look into dct
    :param fn: a procedure to call to get a default value if key is not in dct.
    :return: dct[key] or fn()
    """
    value = dct.get(key, None)
    if value is None:
        value = fn()
    return value


def get_convenient_os_path(long_name):
    """
    (windows)
    Gets the short path name of a given long path.
    http://stackoverflow.com/a/23598461/200291
    (unix)
    Return given name.
    """
    if not sys.platform.startswith('win'):
        return long_name
    import ctypes
    from ctypes import wintypes
    _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
    _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    _GetShortPathNameW.restype = wintypes.DWORD
    output_buf_size = 0
    while True:
        output_buf = ctypes.create_unicode_buffer(output_buf_size)
        needed = _GetShortPathNameW(long_name, output_buf, output_buf_size)
        if output_buf_size >= needed:
            return output_buf.value
        else:
            output_buf_size = needed


def dispatch_tasks(tasks, job_count, next_job_id):
    """ Split <tasks> into <job_count> jobs and associate each one
        with an unique job ID starting from <next_job_id>, so that
        each job could assign an unique ID to each of his task by
        incrementing his job ID when managing his tasks.
    :param tasks: tasks to split
    :param job_count: number of jobs
    :param next_job_id: first job ID to use.
    :return: a list of couples (job, job ID).
    """
    task_count = len(tasks)
    if job_count > task_count:
        job_lengths = [1] * task_count
    else:
        job_lengths = [task_count // job_count] * job_count
        for i in range(task_count % job_count):
            job_lengths[i] += 1
    if sum(job_lengths) != task_count:
        raise ValueError('Programming error when dispatching tasks: total expected %d, got %d'
                         % (task_count, sum(job_lengths)))
    cursor = 0
    jobs = []
    for job_len in job_lengths:
        jobs.append([tasks[cursor:(cursor + job_len)], next_job_id + cursor])
        cursor += job_len
    # NB: next_job_id is now next_job_id + len(tasks).
    return jobs
