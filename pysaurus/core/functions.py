import os
import re
from datetime import datetime

import whirlpool

from pysaurus.core.constants import VIDEO_SUPPORTED_EXTENSIONS

# Datetime since timestamp 0.
EPOCH = datetime.utcfromtimestamp(0)

REGEX_NO_WORD = re.compile(r'(\W|_)+')


def string_to_pieces(the_string):
    return [piece.lower() for piece in REGEX_NO_WORD.sub(' ', the_string).split()]


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


def to_printable(element):
    if isinstance(element, str):
        if '"' in element:
            return "'%s'" % element
        return '"%s"' % element
    return element


def package_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


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


def timestamp_microseconds():
    """ Return current timestamp with microsecond resolution.
        :return: int
    """
    delta = datetime.now() - EPOCH
    return (delta.days * 24 * 60 * 60 + delta.seconds) * 1000000 + delta.microseconds


def whirlpool_hash(string: str):
    return whirlpool.new(string.encode()).hexdigest().lower()


def flat_to_coord(index, width):
    # i => (x, y)
    return index % width, index // width


def coord_to_flat(x, y, width):
    # (x, y) => i
    return y * width + x
