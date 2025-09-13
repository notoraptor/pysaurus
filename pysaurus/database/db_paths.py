import logging
import os
from typing import Self

from pysaurus.application import exceptions
from pysaurus.core import functions
from pysaurus.core.absolute_path import AbsolutePath, PathType

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
    __slots__ = ("is_folder", "create", "_path", "parent", "simple_path")

    def __init__(self, folder, name, suffix, is_folder=False, create_folder=False):
        super().__init__(name, suffix)
        self.parent = AbsolutePath.ensure(folder).assert_dir()
        self.is_folder = is_folder
        self.create = create_folder
        if self.is_folder:
            path = new_sub_folder(folder, self.suffix)
            if self.create:
                path.mkdir()
            simple_path = self.get_simple_folder()
        else:
            path = new_sub_file(folder, self.suffix)
            simple_path = self.get_simple_file()
        self._path = path
        self.simple_path = simple_path
        # Make sure we use simple path instead of old path.
        # Old path is based on database folder, more complicated to maintain
        # (e.g: mydb1/mydb1.file, mydb2/mydb2.file)
        # Simple path is based on path name, same for all database folders
        # (e.g: mydb1/standardname.file, mydb2/standardname.file)
        if self._path.exists():
            assert not self.simple_path.exists()
            os.rename(self._path.path, self.simple_path.path)
            assert self.simple_path.exists()
            assert not self._path.exists()
        elif self.simple_path.exists():
            assert not self._path.exists()

    @property
    def path(self) -> AbsolutePath:
        return self.simple_path

    def with_new_parent(
        self, parent: AbsolutePath, create: bool | None = False
    ) -> Self:
        return (
            self
            if self.parent == parent
            else DatabasePath(
                parent,
                self.name,
                self.suffix,
                is_folder=self.is_folder,
                create_folder=self.create if create is None else create,
            )
        )

    def get_simple_folder(self, sep=".") -> AbsolutePath:
        return AbsolutePath.join(self.parent, f"{self.name}{sep}{self.suffix}")

    def get_simple_file(self) -> AbsolutePath:
        return AbsolutePath.file_path(self.parent, self.name, self.suffix)


class DatabasePaths:
    __slots__ = ("db_folder", "paths")

    def __init__(self, folder: PathType):
        self.db_folder: AbsolutePath = AbsolutePath.ensure(folder).assert_dir()
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

    def renamed(self, new_name: str) -> Self:
        new_name = new_name.strip()
        if new_name == self.db_folder.title:
            return self
        if functions.has_discarded_characters(new_name):
            raise exceptions.InvalidDatabaseName(new_name)
        new_db_folder = AbsolutePath.join(self.db_folder.get_directory(), new_name)
        if new_db_folder.exists():
            raise exceptions.DatabaseAlreadyExists(new_db_folder)
        new_paths = type(self)(new_db_folder.mkdir())
        for old_path in self.paths.values():
            np = old_path.with_new_parent(new_paths.db_folder)
            new_paths.paths[np.name] = np
            if old_path.path.exists():
                os.rename(old_path.path.path, np.path.path)
        for remaining_name in self.db_folder.listdir():
            op = AbsolutePath.join(self.db_folder, remaining_name)
            np = AbsolutePath.join(new_paths.db_folder, remaining_name)
            os.rename(op.path, np.path)
        assert not list(self.db_folder.listdir())
        self.db_folder.delete()
        logger.debug(f"Deleted {self.db_folder}")
        return new_paths


def new_sub_file(folder: AbsolutePath, extension: str) -> AbsolutePath:
    return AbsolutePath.file_path(folder, folder.title, extension)


def new_sub_folder(folder: AbsolutePath, suffix: str, sep=".") -> AbsolutePath:
    return AbsolutePath.join(folder, f"{folder.title}{sep}{suffix}")
