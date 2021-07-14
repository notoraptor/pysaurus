from pathlib import Path
from pysaurus.core.components import AbsolutePath
from pysaurus.core.modules import FileSystem
from pysaurus.core.notifier import DEFAULT_NOTIFIER
from pysaurus.core.database.database import Database
from typing import Dict, Optional, List, Sequence, Iterable
import os


class Application:
    def __init__(self, notifier=DEFAULT_NOTIFIER):
        self.app_name = "Pysaurus"
        self.home_dir = AbsolutePath(str(Path.home()))
        self.app_dir = AbsolutePath.join(self.home_dir, f".{self.app_name}").mkdir()
        self.dbs_dir = AbsolutePath.join(self.app_dir, "databases").mkdir()
        self.databases = {}  # type: Dict[AbsolutePath, Optional[Database]]
        self.notifier = notifier
        for entry in FileSystem.scandir(self.dbs_dir.path):  # type: os.DirEntry
            if entry.is_dir():
                self.databases[AbsolutePath(entry.path)] = None

    def get_database_paths(self) -> List[AbsolutePath]:
        return sorted(self.databases.keys())

    def open_database(self, path: AbsolutePath) -> Database:
        path = AbsolutePath.ensure(path)
        assert path in self.databases
        if not self.databases[path]:
            self.databases[path] = Database(path, notifier=self.notifier)
        return self.databases[path]

    def new_database(self, name, folders: Iterable[AbsolutePath]):
        path = AbsolutePath.join(self.dbs_dir, name)
        if path.title != name:
            raise OSError(
                f"Bad database name: {name}\n"
                f"Please do not use punctuations and special characters."
            )
        if path in self.databases:
            raise OSError(f"Database with same name already exists: {name}")
        if path.exists():
            raise OSError(
                f"Path already exists but is not a database: {path}\n"
                f"Consider remove it manually before creating the database."
            )
        self.databases[path] = Database(
            path.mkdir(), folders=folders, notifier=self.notifier
        )
        return self.databases[path]

    def delete_database(self, path: AbsolutePath):
        if path in self.databases:
            path.delete()
            del self.databases[path]
