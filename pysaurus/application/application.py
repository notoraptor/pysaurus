import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import ujson as json

from pysaurus.application import exceptions
from pysaurus.application.config import Config
from pysaurus.application.utils import package_dir
from pysaurus.core import functions
from pysaurus.core.components import AbsolutePath
from pysaurus.core.custom_json_parser import parse_json
from pysaurus.core.dict_file_format import dff_dump, dff_load
from pysaurus.core.modules import FileSystem
from pysaurus.core.notifier import DEFAULT_NOTIFIER
from pysaurus.database.database import Database
from pysaurus.language.default_language import DefaultLanguage, language_to_dict
from pysaurus.language.language import Language
from saurus.language import say


class Application:
    app_name = "Pysaurus"

    def __init__(self, notifier=DEFAULT_NOTIFIER):
        self.home_dir = AbsolutePath(str(Path.home()))
        self.app_dir = AbsolutePath.join(self.home_dir, f".{self.app_name}").mkdir()
        self.dbs_dir = AbsolutePath.join(self.app_dir, "databases").mkdir()
        self.lang_dir = AbsolutePath.join(self.app_dir, "languages").mkdir()
        self.config_path = AbsolutePath.join(self.app_dir, "config.json")
        self.config = Config()
        self.databases = {}  # type: Dict[AbsolutePath, Optional[Database]]
        self.languages = {}  # type: Dict[AbsolutePath, Optional[DefaultLanguage]]
        self.notifier = notifier
        # Load database names.
        for entry in FileSystem.scandir(self.dbs_dir.path):  # type: os.DirEntry
            if entry.is_dir():
                self.databases[AbsolutePath(entry.path)] = None
        # Load language names.
        for entry in FileSystem.scandir(self.lang_dir.path):  # type: os.DirEntry
            path = AbsolutePath(entry.path)
            if path.isfile() and path.extension == "txt":
                self.languages[path] = None
        # Load default languages names.
        for entry in FileSystem.scandir(
            os.path.join(package_dir(), "language", "default")
        ):
            path = AbsolutePath(entry.path)
            if path.isfile() and path.extension == "txt":
                print("Checking embedded language", path.title)
                user_path = AbsolutePath.join(self.lang_dir, path.get_basename())
                if user_path in self.languages:
                    if user_path.get_date_modified() < path.get_date_modified():
                        user_path.delete()
                        path.copy_file_to(user_path)
                        print("Updated embedded language", path.title)
                    else:
                        print("User language more up-to-date", path.title)
                else:
                    path.copy_file_to(user_path)
                    self.languages[user_path] = None
                    print("Installed embedded language", path.title)
        # Load config file.
        if self.config_path.exists():
            assert self.config_path.isfile()
            self.config.update(parse_json(self.config_path))
        # Load language.
        lang_path = AbsolutePath.join(self.lang_dir, f"{self.config.language}.txt")
        if lang_path not in self.languages:
            if self.config.language == DefaultLanguage.__language__:
                print(
                    "[Default language]", DefaultLanguage.__language__, file=sys.stderr
                )
                dff_dump(language_to_dict(DefaultLanguage, extend=False), lang_path)
            else:
                raise exceptions.MissingLanguageFile(self.config.language)
        self.languages[lang_path] = self._load_lang(lang_path)
        say.set_language(self.config.language)
        say.set_folder(AbsolutePath.join(self.app_dir, "lang").mkdir())

    def _load_lang(self, lang_path: AbsolutePath):
        lang = Language(dff_load(lang_path), self.config.language)
        if lang.__updated__:
            print("[language updated]", lang_path.title)
            dff_dump(language_to_dict(lang, extend=False), lang_path)
        return lang

    @property
    def lang(self) -> DefaultLanguage:
        return self.languages[
            AbsolutePath.join(self.lang_dir, f"{self.config.language}.txt")
        ]

    def get_database_names(self) -> List[str]:
        return sorted(path.title for path in self.databases.keys())

    def open_database_from_name(self, name: str) -> Database:
        path = AbsolutePath.join(self.dbs_dir, name)
        assert path in self.databases
        if not self.databases[path]:
            self.databases[path] = Database(
                path, notifier=self.notifier, lang=self.lang
            )
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
            path.mkdir(), folders=folders, notifier=self.notifier, lang=self.lang
        )
        return self.databases[path]

    def delete_database_from_name(self, name: str):
        path = AbsolutePath.join(self.dbs_dir, name)
        if path in self.databases:
            path.delete()
            del self.databases[path]
            return True

    def get_language_paths(self) -> List[AbsolutePath]:
        return sorted(self.languages.keys())

    def open_language(self, lang_path: AbsolutePath) -> DefaultLanguage:
        lang_path = AbsolutePath.ensure(lang_path)
        assert lang_path in self.languages
        self.config.language = lang_path.title
        if not self.languages[lang_path]:
            self.languages[lang_path] = self._load_lang(lang_path)
        self.save_config()
        return self.lang

    def open_language_from_name(self, name: str) -> DefaultLanguage:
        return self.open_language(AbsolutePath.join(self.lang_dir, f"{name}.txt"))

    def save_config(self):
        with open(self.config_path.path, "w") as file:
            json.dump(self.config.to_json(), file)
