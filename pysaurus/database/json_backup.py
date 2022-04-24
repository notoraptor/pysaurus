import ujson as json

from pysaurus.core.components import AbsolutePath, PathType
from pysaurus.database.db_utils import flush_json_data


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
