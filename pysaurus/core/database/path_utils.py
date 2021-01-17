from typing import Iterable, Union

from pysaurus.core.components import AbsolutePath, FilePath
from pysaurus.core.constants import THUMBNAIL_EXTENSION
from pysaurus.core.modules import FNV64


def generate_thumb_name(file_name):
    # type: (AbsolutePath) -> str
    return FNV64.hash(file_name.standard_path)


def generate_thumb_path(folder, thumb_name):
    # type: (AbsolutePath, str) -> AbsolutePath
    return FilePath(folder, thumb_name, THUMBNAIL_EXTENSION)


def load_list_file(list_file_path):
    # type: (Union[AbsolutePath, str]) -> Iterable[str]
    strings = []
    list_file_path = AbsolutePath.ensure(list_file_path)
    if list_file_path.isfile():
        with open(list_file_path.path, "r") as list_file:
            for line in list_file:
                line = line.strip()
                if line and line[0] != "#":
                    strings.append(line)
    return strings


def load_path_list_file(list_file_path):
    # type: (AbsolutePath) -> Iterable[AbsolutePath]
    return [AbsolutePath(string) for string in load_list_file(list_file_path)]
