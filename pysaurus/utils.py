import codecs
import os
from io import StringIO


def __load_extensions():
    """ Load video supported extensions from `PACKAGE_DIR/pysaurus/extensions.txt` in a frozen set. """
    extensions = []
    extension_filename = os.path.join(os.path.dirname(__file__), 'extensions.txt')
    with open(extension_filename, 'r') as extension_file:
        for line in extension_file.readlines():
            line = line.strip()
            if line and not line.startswith('#'):
                extensions.append(line.lower())
    return frozenset(extensions)


VIDEO_SUPPORTED_EXTENSIONS = __load_extensions()
THUMBNAIL_EXTENSION = 'png'


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
        if not isinstance(message, str):
            message = str(message)
        line = character * len(message)
        self.write(line)
        self.write(message)
