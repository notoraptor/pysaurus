import logging

from pysaurus.application import exceptions
from pysaurus.core import functions
from pysaurus.core.components import AbsolutePath, PathType
from pysaurus.core.modules import FileSystem

logger = logging.getLogger(__name__)


class DbPaths:
    __slots__ = (
        "db_folder",
        "thumb_folder",
        "json_path",
        "miniatures_path",
        "log_path",
        "index_path",
    )

    def __init__(self, path: PathType, create_thumb_folder=True):
        self.db_folder = AbsolutePath.ensure_directory(path)
        self.thumb_folder = new_sub_folder(self.db_folder, "thumbnails")
        self.json_path = new_sub_file(self.db_folder, "json")
        self.miniatures_path = new_sub_file(self.db_folder, "miniatures.json")
        self.log_path = new_sub_file(self.db_folder, "log")
        self.index_path = new_sub_file(self.db_folder, "db")
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
        if self.miniatures_path.exists():
            FileSystem.rename(self.miniatures_path.path, new_paths.miniatures_path.path)
        if self.log_path.exists():
            FileSystem.rename(self.log_path.path, new_paths.log_path.path)
        if self.index_path.exists():
            FileSystem.rename(self.index_path.path, new_paths.index_path.path)
        self.db_folder.delete()
        logger.debug(f"Deleted {self.db_folder}")
        return new_paths


def new_sub_file(folder: AbsolutePath, extension: str) -> AbsolutePath:
    return AbsolutePath.file_path(folder, folder.title, extension)


def new_sub_folder(folder: AbsolutePath, suffix: str, sep=".") -> AbsolutePath:
    return AbsolutePath.join(folder, f"{folder.title}{sep}{suffix}")
