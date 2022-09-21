import ujson as json

from pysaurus.core.components import AbsolutePath, PathType
from pysaurus.core.modules import FileSystem


class JsonBackup:
    __slots__ = ("__json_path", "__thumb_folder", "__prev_path", "__next_path")

    def __init__(self, path: PathType):
        path = AbsolutePath.ensure(path)
        folder = path.get_directory()
        self.__json_path = path
        self.__prev_path = AbsolutePath.file_path(folder, path.title, "prev.json")
        self.__next_path = AbsolutePath.file_path(folder, path.title, "next.json")
        self.__thumb_folder = AbsolutePath.join(folder, f"{path.title}.thumbnails")

    path = property(lambda self: self.__json_path)
    thumbnail_folder = property(lambda self: self.__thumb_folder)

    def load(self):
        data = {}
        if self.__json_path.exists():
            with open(self.__json_path.assert_file().path) as output_file:
                data = json.load(output_file)
        return data

    def save(self, json_output):
        flush_json_data(
            json_output, self.__prev_path, self.__json_path, self.__next_path
        )


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
