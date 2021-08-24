# import atexit
import json
import os
from pathlib import Path
from typing import Dict, Optional, List, Iterable

from pysaurus.application import exceptions
from pysaurus.application.config import Config
from pysaurus.application.default_language import DefaultLanguage
from pysaurus.application.language import Language
from pysaurus.core import functions
from pysaurus.core.components import AbsolutePath
from pysaurus.core.custom_json_parser import parse_json
from pysaurus.database.database import Database
from pysaurus.core.modules import FileSystem
from pysaurus.core.notifier import DEFAULT_NOTIFIER


class Application:
    lang = None

    def __init__(self, notifier=DEFAULT_NOTIFIER):
        self.app_name = "Pysaurus"
        self.home_dir = AbsolutePath(str(Path.home()))
        self.app_dir = AbsolutePath.join(self.home_dir, f".{self.app_name}").mkdir()
        self.dbs_dir = AbsolutePath.join(self.app_dir, "databases").mkdir()
        self.lang_dir = AbsolutePath.join(self.app_dir, "languages").mkdir()
        self.config_path = AbsolutePath.join(self.app_dir, "config.json")
        self.config = Config()
        self.databases = {}  # type: Dict[AbsolutePath, Optional[Database]]
        self.notifier = notifier
        # Load database names.
        for entry in FileSystem.scandir(self.dbs_dir.path):  # type: os.DirEntry
            if entry.is_dir():
                self.databases[AbsolutePath(entry.path)] = None
        # Load config file.
        if self.config_path.exists():
            assert self.config_path.isfile()
            self.config.update(parse_json(self.config_path))
        # Load language.
        lang_path = AbsolutePath.join(self.lang_dir, f"{self.config.language}.json")
        if lang_path.exists():
            assert lang_path.isfile()
        elif self.config.language == DefaultLanguage.__language__:
            default_dct = {
                key: getattr(DefaultLanguage, key)
                for key in functions.class_get_public_attributes(DefaultLanguage)
            }
            with open(lang_path.path, "w") as file:
                json.dump(default_dct, file, indent="\t")
        else:
            raise exceptions.MissingLanguageFile(self.config.language)
        self.lang = Language(parse_json(lang_path))

    def get_database_paths(self) -> List[AbsolutePath]:
        return sorted(self.databases.keys())

    def open_database(self, path: AbsolutePath) -> Database:
        path = AbsolutePath.ensure(path)
        assert path in self.databases
        if not self.databases[path]:
            self.databases[path] = Database(path, notifier=self.notifier)
        return self.databases[path]

    def new_database(self, name, folders: Iterable[AbsolutePath]):
        if functions.has_discarded_characters(name):
            raise exceptions.InvalidDatabaseName(name)
        path = AbsolutePath.join(self.dbs_dir, name)
        if path.title != name:
            raise exceptions.InvalidDatabaseName(name)
        if path in self.databases:
            raise exceptions.DatabaseAlreadyExists(path)
        if path.exists():
            raise exceptions.DatabasePathUnavailable(path)
        self.databases[path] = Database(
            path.mkdir(), folders=folders, notifier=self.notifier
        )
        return self.databases[path]

    def delete_database(self, path: AbsolutePath):
        if path in self.databases:
            path.delete()
            del self.databases[path]
            return True
