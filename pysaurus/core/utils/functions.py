import codecs
import os

from pysaurus.core.utils.constants import VIDEO_SUPPORTED_EXTENSIONS


def is_valid_video_filename(filename):
    _, extension = os.path.splitext(filename)
    return extension and extension[1:].lower() in VIDEO_SUPPORTED_EXTENSIONS


def dispatch_tasks(tasks, job_count, extra_args=None):
    # type: (list, int, list) -> list
    """ Split <tasks> into <job_count> jobs and associate each one
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
        raise ValueError('Programming error when dispatching tasks: total expected %d, got %d.'
                         % (task_count, sum(job_lengths)))
    cursor = 0
    jobs = []
    job_id = 0
    job_count = len(job_lengths)
    for job_len in job_lengths:
        job_id += 1
        jobs.append([tasks[cursor:(cursor + job_len)], '%d/%d' % (job_id, job_count)] + extra_args)
        cursor += job_len
    # NB: next_job_id is now next_job_id + len(tasks).
    return jobs


def print_title(message, wrapper='='):
    message = str(message)
    len_message = len(message)
    line = wrapper * len_message
    print(line)
    print(message)
    print(line)


def hex_to_string(message):
    return codecs.decode(message, 'hex').decode()


def permute(values, initial_permutation=()):
    """ Generate a sequence of permutations from given values list. """
    initial_permutation = list(initial_permutation)
    if not values:
        yield initial_permutation
        return
    for position in range(len(values)):
        extended_permutation = initial_permutation + [values[position]]
        remaining_values = values[:position] + values[(position + 1):]
        for permutation in permute(remaining_values, extended_permutation):
            yield permutation


def file_system_is_case_insensitive(folder='.'):
    base_name = os.path.join(folder, 'tmp')
    count = 0
    while True:
        test_name = '%s%d' % (base_name, count)
        if os.path.exists(test_name):
            count += 1
        else:
            break
    with open(test_name, 'w+'):
        is_insensitive = os.path.exists(test_name.upper())
    os.unlink(test_name)
    return is_insensitive


def is_iterable(element):
    return isinstance(element, (list, tuple, set))


def ensure_set(iterable):
    if not isinstance(iterable, set):
        iterable = set(iterable)
    return iterable


def to_printable(element):
    if isinstance(element, str):
        if '"' in element:
            return "'%s'" % element
        return '"%s"' % element
    return element


def package_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def enumeration(values):
    class Enumeration:
        __slots__ = 'values',

        def __init__(self, values):
            self.values = set(values)

        def __call__(self, value):
            if value not in self.values:
                raise ValueError('Invalid value\n\tGot: %s\n\tExpected:%s\n' % (value, self.values))
            return value

    enum_instance = Enumeration(values)

    def enum_parser(value):
        return enum_instance(value)

    enum_parser.__name__ = '{%s}' % (', '.join(enum_instance.values))
    return enum_parser


def longest_prefix(a, b):
    # type: (str, str) -> str
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            return a[:i]
    return a if len(a) < len(b) else b


def longest_common_path(a, b):
    pieces_a = a.split(os.sep)
    pieces_b = b.split(os.sep)
    for i in range(min(len(pieces_a), len(pieces_b))):
        if pieces_a[i] != pieces_b[i]:
            return os.sep.join(pieces_a[:i])
    return a if len(a) < len(b) else b


def bool_type(mixed):
    """ Convert a value to a boolean, with following rules (in that order):
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
        if mixed.lower() == 'true':
            return True
        if not mixed or mixed.lower() == 'false':
            return False
        try:
            return bool(int(mixed))
        except ValueError:
            try:
                return bool(float(mixed))
            except ValueError:
                pass
    return bool(mixed)
