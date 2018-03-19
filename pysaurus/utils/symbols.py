import os
import whirlpool
from datetime import datetime

PACKAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..'))


def __load_extensions():
    """ Load video supported extensions from `PACKAGE_DIR/pysaurus/extensions.txt` in a frozen set. """
    extensions = []
    extension_filename = os.path.join(PACKAGE_DIR, 'pysaurus', 'utils', 'extensions.txt')
    with open(extension_filename, 'r') as extension_file:
        for line in extension_file.readlines():
            line = line.strip()
            if line and not line.startswith('#'):
                extensions.append(line)
    return frozenset(extensions)


def timestamp_microseconds():
    """ Return current timestamp with microsecond resolution. """
    current_time = datetime.now()
    epoch = datetime.utcfromtimestamp(0)
    delta = current_time - epoch
    return (delta.days * 24 * 60 * 60 + delta.seconds) * 1000000 + delta.microseconds


def is_sequence(variable):
    return hasattr(variable, '__iter__')


VIDEO_SUPPORTED_EXTENSIONS = __load_extensions()


def is_valid_video_filename(filename):
    _, extension = os.path.splitext(filename)
    return extension and extension[1:] in VIDEO_SUPPORTED_EXTENSIONS


def hash_with_whirlpool(string: str):
    wp = whirlpool.new(string.encode())
    return wp.hexdigest().upper()
