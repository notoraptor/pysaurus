import logging

from pysaurus.application import exceptions
from pysaurus.core import functions
from pysaurus.core.components import AbsolutePath, PathType
from pysaurus.core.modules import FileSystem

logger = logging.getLogger(__name__)


class DatabasePathDef:
    __slots__ = ("name", "suffix")

    def __init__(self, name: str, suffix: str):
        self.name = name
        self.suffix = suffix

    def __str__(self):
        return self.name


DatabasePathName = str | DatabasePathDef


class DatabasePath(DatabasePathDef):
    __slots__ = ("is_folder", "create", "path")

    def __init__(self, folder, name, suffix, is_folder=False, create_folder=False):
        super().__init__(name, suffix)
        self.is_folder = is_folder
        self.create = create_folder
        if self.is_folder:
            path = new_sub_folder(folder, self.suffix)
            if self.create:
                path.mkdir()
        else:
            path = new_sub_file(folder, self.suffix)
        self.path = path


class DatabasePaths:
    __slots__ = ("db_folder", "paths")

    def __init__(self, folder: PathType):
        self.db_folder: AbsolutePath = AbsolutePath.ensure_directory(folder)
        self.paths: dict[str, DatabasePath] = {}

    def __iter__(self):
        yield ".", self.db_folder
        for key, value in self.paths.items():
            yield str(key), value.path

    def define_file(self, name: str, extension: str) -> AbsolutePath:
        assert name not in self.paths
        self.paths[name] = DatabasePath(self.db_folder, name, extension)
        return self.paths[name].path

    def define_folder(self, name, suffix, create=True) -> AbsolutePath:
        assert name not in self.paths
        self.paths[name] = DatabasePath(self.db_folder, name, suffix, True, create)
        return self.paths[name].path

    def define(
        self, definition: DatabasePathDef, is_folder=False, create_folder=False
    ) -> AbsolutePath:
        if is_folder:
            return self.define_folder(definition.name, definition.suffix, create_folder)
        else:
            return self.define_file(definition.name, definition.suffix)

    def get(self, name: DatabasePathName) -> AbsolutePath:
        return self.paths[str(name)].path

    def renamed(self, new_name: str):
        new_name = new_name.strip()
        if new_name == self.db_folder.title:
            return self
        if functions.has_discarded_characters(new_name):
            raise exceptions.InvalidDatabaseName(new_name)
        new_db_folder = AbsolutePath.join(self.db_folder.get_directory(), new_name)
        if new_db_folder.exists():
            raise exceptions.DatabaseAlreadyExists(new_db_folder)
        new_paths = DatabasePaths(new_db_folder.mkdir())
        for path in self.paths.values():
            path_exists = path.path.exists()
            if path.is_folder:
                np = new_paths.define_folder(path.name, path.suffix, not path_exists)
            else:
                np = new_paths.define_file(path.name, path.suffix)
            if path_exists:
                FileSystem.rename(path.path.path, np.path)
        for remaining_name in self.db_folder.listdir():
            op = AbsolutePath.join(self.db_folder, remaining_name)
            if remaining_name.startswith(f"{self.db_folder.title}."):
                dec = len(self.db_folder.title)
                np = AbsolutePath.join(
                    new_paths.db_folder,
                    f"{new_paths.db_folder.title}.{remaining_name[(dec + 1) :]}",
                )
            else:
                np = AbsolutePath.join(new_paths.db_folder, remaining_name)
            FileSystem.rename(op.path, np.path)
        assert not list(self.db_folder.listdir())
        self.db_folder.delete()
        logger.debug(f"Deleted {self.db_folder}")
        return new_paths


def new_sub_file(folder: AbsolutePath, extension: str) -> AbsolutePath:
    return AbsolutePath.file_path(folder, folder.title, extension)


def new_sub_folder(folder: AbsolutePath, suffix: str, sep=".") -> AbsolutePath:
    return AbsolutePath.join(folder, f"{folder.title}{sep}{suffix}")
