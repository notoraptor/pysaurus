import sys

from pysaurus.application import exceptions
from pysaurus.core import functions
from pysaurus.core.components import AbsolutePath, PathType
from pysaurus.core.modules import FileSystem


class DbPaths:
    __slots__ = (
        "db_folder",
        "thumb_folder",
        "json_path",
        "miniatures_path",
        "log_path",
    )

    def __init__(self, path: PathType, create_thumb_folder=True):
        self.db_folder = AbsolutePath.ensure_directory(path)
        self.thumb_folder = new_sub_folder(self.db_folder, "thumbnails")
        self.json_path = new_sub_file(self.db_folder, "json")
        self.miniatures_path = new_sub_file(self.db_folder, "miniatures.json")
        self.log_path = new_sub_file(self.db_folder, "log")
        if create_thumb_folder:
            self.thumb_folder.mkdir()

    def renamed(self, new_name: str):
        new_name = new_name.strip()
        if new_name == self.db_folder.title:
            return self
        if functions.has_discarded_characters(new_name):
            raise exceptions.InvalidDatabaseName(new_name)
        new_db_folder = AbsolutePath.join(self.db_folder.get_directory(), new_name)
        if new_db_folder.exists():
            raise exceptions.DatabaseAlreadyExists(new_db_folder)
        new_paths = DbPaths(new_db_folder.mkdir(), create_thumb_folder=False)
        FileSystem.rename(self.thumb_folder.path, new_paths.thumb_folder.path)
        FileSystem.rename(self.json_path.path, new_paths.json_path.path)
        FileSystem.rename(self.miniatures_path.path, new_paths.miniatures_path.path)
        FileSystem.rename(self.log_path.path, new_paths.log_path.path)
        self.db_folder.delete()
        print("Deleted", self.db_folder, file=sys.stderr)
        return new_paths


def new_sub_file(folder: AbsolutePath, extension: str) -> AbsolutePath:
    return AbsolutePath.file_path(folder, folder.title, extension)


def new_sub_folder(folder: AbsolutePath, suffix: str, sep=".") -> AbsolutePath:
    return AbsolutePath.join(folder, f"{folder.title}{sep}{suffix}")
