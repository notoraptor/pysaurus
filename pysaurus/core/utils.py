import codecs
import os
from io import StringIO

import whirlpool
from pysaurus.core.absolute_path import AbsolutePath

VIDEO_SUPPORTED_EXTENSIONS = frozenset(
    ('3g2', '3gp', 'asf', 'avi', 'drc', 'f4a', 'f4b', 'f4p', 'f4v', 'flv', 'gifv', 'm2v', 'm4p', 'm4v', 'mkv', 'mng',
     'mov', 'mp2', 'mp4', 'mpe', 'mpeg', 'mpg', 'mpv', 'mxf', 'nsv', 'ogg', 'ogv', 'qt', 'rm', 'rmvb', 'roq', 'svi',
     'vob', 'webm', 'wmv', 'yuv'))

assert len(VIDEO_SUPPORTED_EXTENSIONS) == 36, (len(VIDEO_SUPPORTED_EXTENSIONS), VIDEO_SUPPORTED_EXTENSIONS)


def is_valid_video_filename(filename):
    _, extension = os.path.splitext(filename)
    return extension and extension[1:].lower() in VIDEO_SUPPORTED_EXTENSIONS


def dispatch_tasks(tasks, job_count, next_job_id=0):
    """ Split <tasks> into <job_count> jobs and associate each one
        with an unique job ID starting from <next_job_id>, so that
        each job could assign an unique ID to each of his task by
        incrementing his job ID when managing his tasks.
        :param tasks: a list of tasks to split.
        :param job_count: number of jobs.
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
        raise ValueError('Programming error when dispatching tasks: total expected %d, got %d.'
                         % (task_count, sum(job_lengths)))
    cursor = 0
    jobs = []
    for job_len in job_lengths:
        jobs.append([tasks[cursor:(cursor + job_len)], next_job_id + cursor])
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


def load_path_list_file(list_file_path: AbsolutePath):
    paths = set()
    if list_file_path.isfile():
        with open(list_file_path.path, 'r') as list_file:
            for line in list_file:
                line = line.strip()
                if line and line[0] != '#':
                    paths.add(AbsolutePath(line))
    return paths


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

    def title(self, message, character='=', up=True, down=False):
        if not isinstance(message, str):
            message = str(message)
        line = character * len(message)
        if up:
            self.write(line)
        self.write(message)
        if down:
            self.write(line)


class Whirlpool:
    wp = None

    @staticmethod
    def hash(string: str):
        if not Whirlpool.wp:
            Whirlpool.wp = whirlpool.new()
        Whirlpool.wp.update(string.encode())
        return Whirlpool.wp.hexdigest().lower()
