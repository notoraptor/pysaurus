from typing import Set

from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.utils.classes import Whirlpool
from pysaurus.core.utils.constants import THUMBNAIL_EXTENSION


def generate_thumb_name(file_name):
    # type: (AbsolutePath) -> str
    return Whirlpool.hash(file_name.standard_path)


def generate_thumb_path(folder, thumb_name):
    # type: (AbsolutePath, str) -> AbsolutePath
    return AbsolutePath.new_file_path(folder, thumb_name, THUMBNAIL_EXTENSION)


def load_path_list_file(list_file_path):
    # type: (AbsolutePath) -> Set[AbsolutePath]
    paths = set()
    if list_file_path.isfile():
        with open(list_file_path.path, 'r') as list_file:
            for line in list_file:
                line = line.strip()
                if line and line[0] != '#':
                    paths.add(AbsolutePath(line))
    return paths
