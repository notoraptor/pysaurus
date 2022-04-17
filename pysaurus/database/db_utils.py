import ujson as json

from pysaurus.core.components import AbsolutePath
from pysaurus.core.constants import THUMBNAIL_EXTENSION
from pysaurus.core.modules import FNV64, FileSystem


def new_sub_file(folder: AbsolutePath, extension: str):
    return AbsolutePath.file_path(folder, folder.title, extension)


def new_sub_folder(folder: AbsolutePath, suffix: str, sep="."):
    return AbsolutePath.join(folder, f"{folder.title}{sep}{suffix}")


def generate_thumb_name(file_name):
    # type: (AbsolutePath) -> str
    return FNV64.hash(file_name.standard_path)


def generate_thumb_path(folder, thumb_name):
    # type: (AbsolutePath, str) -> AbsolutePath
    return AbsolutePath.file_path(folder, thumb_name, THUMBNAIL_EXTENSION)


def flush_json_data(
    data: object,
    previous_file_path: AbsolutePath,
    target_file_path: AbsolutePath,
    next_file_path: AbsolutePath,
):
    # Store JSON data to next file
    with open(next_file_path.path, "w") as output_file:
        json.dump(data, output_file)
    # Remove previous file
    previous_file_path.delete()
    # Move target file to previous file
    if target_file_path.isfile():
        FileSystem.rename(target_file_path.path, previous_file_path.path)
        assert not target_file_path.isfile()
        assert previous_file_path.isfile()
    # Move next file to target file
    FileSystem.rename(next_file_path.path, target_file_path.path)
    # Next file deleted
    # Previous file may exists
    # Target file contains data
    assert not next_file_path.exists()
    assert target_file_path.isfile()
