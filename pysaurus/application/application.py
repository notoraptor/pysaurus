from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import ujson as json

from pysaurus.application import exceptions
from pysaurus.core import functions, language
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.custom_json_parser import parse_json
from pysaurus.core.modules import FileSystem
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.core.profiling import Profiler
from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.database.database import Database


@dataclass(slots=True)
class Config:
    language: str = "en"


class Application:
    __slots__ = (
        "home_dir",
        "app_dir",
        "dbs_dir",
        "config_path",
        "config",
        "databases",
        "notifier",
    )
    app_name = "Pysaurus"

    def __init__(
        self, notifier=DEFAULT_NOTIFIER, home_dir: str | AbsolutePath | None = None
    ):
        if home_dir is not None:
            home_dir = AbsolutePath.ensure(home_dir)
        else:
            home_dir = AbsolutePath(str(Path.home()))
        self.home_dir = home_dir
        self.app_dir = (self.home_dir / f".{self.app_name}").mkdir()
        self.dbs_dir = (self.app_dir / "databases").mkdir()
        self.config_path = self.app_dir / "config.json"
        self.config = Config()
        self.databases: dict[AbsolutePath, AbstractDatabase | None] = {}
        self.notifier = notifier
        # Load database names.
        for entry in FileSystem.scandir(self.dbs_dir.path):
            if entry.is_dir() and not entry.name.startswith("."):
                self.databases[AbsolutePath(entry.path)] = None

        # Load config file.
        if self.config_path.exists():
            assert self.config_path.isfile()
            self.config = Config(**parse_json(self.config_path))
        # Normalize legacy full-name identifiers ("english") to ISO 639-1 codes.
        self.config.language = language.canonical_language(self.config.language)
        language.set_language(self.config.language)

    def get_database_names(self) -> list[str]:
        return sorted(path.title for path in self.databases.keys())

    @Profiler.profile_method()
    def open_database_from_name(self, name: str, update=False) -> AbstractDatabase:
        path = self.dbs_dir / name
        assert path in self.databases
        if self.databases[path] is None:
            database = Database(path, notifier=self.notifier, app_dir=self.app_dir)
            self.databases[path] = database
        else:
            database = self.databases[path]
            assert database is not None
            database.reopen()
        if update:
            database.algos.refresh()
        return database

    @Profiler.profile_method()
    def new_database(self, name, folders: Iterable[AbsolutePath], update=False):
        if functions.has_discarded_characters(name):
            raise exceptions.InvalidDatabaseName(name)
        path = self.dbs_dir / name
        if path.title != name:
            raise exceptions.InvalidDatabaseName(name)
        if path in self.databases:
            raise exceptions.DatabaseAlreadyExists(path)
        if path.exists():
            raise exceptions.DatabasePathUnavailable(path)
        database = Database(
            path.mkdir(), folders=folders, notifier=self.notifier, app_dir=self.app_dir
        )
        self.databases[path] = database
        if update:
            database.algos.refresh()
        return database

    def delete_database_from_name(self, name: str):
        path = self.dbs_dir / name
        if path in self.databases:
            self.databases.pop(path)
            path.delete()
            return True

    def get_language_names(self) -> list[str]:
        return language.available_languages()

    def set_language(self, name: str) -> None:
        if name not in language.available_languages():
            raise exceptions.UnknownLanguage(name)
        self.config.language = name
        self.save_config()
        language.set_language(name)

    def save_config(self):
        with open(self.config_path.path, "w") as file:
            json.dump(asdict(self.config), file)

    def __close__(self):
        """Close application."""
        for database in self.databases.values():
            if database:
                database.__close__()
