import logging
import os
from dataclasses import dataclass
from typing import Self, Iterable

from pysaurus.application import exceptions
from pysaurus.core import functions
from pysaurus.core.absolute_path import AbsolutePath, PathType

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Basename:
    name: str
    extension: str = ""


class DatabasePaths:
    __slots__ = ("db_folder", "paths")

    def __init__(self, folder: PathType, basenames: Iterable[Basename] = ()) -> None:
        self.db_folder: AbsolutePath = AbsolutePath.ensure(folder).assert_dir()
        self.paths: dict[str, AbsolutePath] = {}
        for basename in basenames:
            self.add_path(basename)

    def __iter__(self) -> Iterable[tuple[str, AbsolutePath]]:
        yield ".", self.db_folder
        for key, value in self.paths.items():
            yield key, value

    def add_path(self, basename: Basename) -> AbsolutePath:
        name = basename.name
        suffix = basename.extension
        assert name not in self.paths
        self.paths[name] = AbsolutePath.compose(self.db_folder, name, suffix)
        return self.paths[name]

    def get_path(self, basename: Basename) -> AbsolutePath:
        return self.paths[basename.name]

    def renamed(self, new_name: str) -> Self:
        new_name = new_name.strip()
        if new_name == self.db_folder.title:
            return self
        if functions.has_discarded_characters(new_name):
            raise exceptions.InvalidDatabaseName(new_name)
        new_db_folder = self.db_folder.get_directory() / new_name
        if new_db_folder.exists():
            raise exceptions.DatabaseAlreadyExists(new_db_folder)
        new_paths = DatabasePaths(new_db_folder.mkdir())
        for name, old_path in self.paths.items():
            np = AbsolutePath.join(new_paths.db_folder, old_path.get_basename())
            new_paths.paths[name] = np
            if old_path.exists():
                os.rename(old_path.path, np.path)
        for remaining_name in self.db_folder.listdir():
            op = self.db_folder / remaining_name
            np = new_paths.db_folder / remaining_name
            os.rename(op.path, np.path)
        assert not list(self.db_folder.listdir())
        self.db_folder.delete()
        logger.debug(f"Deleted {self.db_folder}")
        return new_paths
