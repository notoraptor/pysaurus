import sys

from pysaurus.application import exceptions
from pysaurus.core import functions
from pysaurus.core.components import AbsolutePath, PathType
from pysaurus.core.modules import FileSystem


class DbPaths:
    __slots__ = (
        "__db_folder",
        "__thumb_folder",
        "__json_path",
        "__miniatures_path",
        "__log_path",
    )

    def __init__(self, path: PathType, create_thumb_folder=True):
        self.__db_folder = AbsolutePath.ensure_directory(path)
        self.__thumb_folder = new_sub_folder(self.__db_folder, "thumbnails")
        self.__json_path = new_sub_file(self.__db_folder, "json")
        self.__miniatures_path = new_sub_file(self.__db_folder, "miniatures.json")
        self.__log_path = new_sub_file(self.__db_folder, "log")
        if create_thumb_folder:
            self.__thumb_folder.mkdir()

    db_folder = property(lambda self: self.__db_folder)
    thumb_folder = property(lambda self: self.__thumb_folder)
    json_path = property(lambda self: self.__json_path)
    miniatures_path = property(lambda self: self.__miniatures_path)
    log_path = property(lambda self: self.__log_path)

    def renamed(self, new_name: str):
        new_name = new_name.strip()
        if new_name == self.__db_folder.title:
            return self
        if functions.has_discarded_characters(new_name):
            raise exceptions.InvalidDatabaseName(new_name)
        new_db_folder = AbsolutePath.join(self.__db_folder.get_directory(), new_name)
        if new_db_folder.exists():
            raise exceptions.DatabaseAlreadyExists(new_db_folder)
        new_paths = DbPaths(new_db_folder.mkdir(), create_thumb_folder=False)
        FileSystem.rename(self.__thumb_folder.path, new_paths.thumb_folder.path)
        FileSystem.rename(self.__json_path.path, new_paths.json_path.path)
        FileSystem.rename(self.__miniatures_path.path, new_paths.miniatures_path.path)
        FileSystem.rename(self.__log_path.path, new_paths.log_path.path)
        self.__db_folder.delete()
        print("Deleted", self.__db_folder, file=sys.stderr)
        return new_paths


def new_sub_file(folder: AbsolutePath, extension: str) -> AbsolutePath:
    return AbsolutePath.file_path(folder, folder.title, extension)


def new_sub_folder(folder: AbsolutePath, suffix: str, sep=".") -> AbsolutePath:
    return AbsolutePath.join(folder, f"{folder.title}{sep}{suffix}")
