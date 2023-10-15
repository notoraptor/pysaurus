import os
from pathlib import Path
from typing import Any, Dict, List

from pysaurus.application.application import Config
from pysaurus.core.components import AbsolutePath
from pysaurus.core.custom_json_parser import parse_json
from pysaurus.core.modules import FileSystem
from saurus.language import say


class PysaurusProgram:
    __slots__ = (
        "home_dir",
        "app_dir",
        "dbs_dir",
        "lang_dir",
        "config_path",
        "config",
        "databases",
    )
    app_name = "Pysaurus"

    def __init__(self):
        self.home_dir = AbsolutePath(str(Path.home()))
        self.app_dir = AbsolutePath.join(self.home_dir, f".{self.app_name}").mkdir()
        self.dbs_dir = AbsolutePath.join(self.app_dir, "databases").mkdir()
        self.databases: Dict[AbsolutePath, Any] = {}
        # Load database names.
        for entry in FileSystem.scandir(self.dbs_dir.path):  # type: os.DirEntry
            if entry.is_dir():
                self.databases[AbsolutePath(entry.path)] = None
        # Load config
        self.config = Config()
        self.config_path = AbsolutePath.join(self.app_dir, "config.json")
        if self.config_path.exists():
            assert self.config_path.isfile()
            self.config = Config(parse_json(self.config_path))
        # TODO Load lang (not yet correctly handled)
        self.lang_dir = AbsolutePath.join(self.app_dir, "lang").mkdir()
        say.set_language(self.config.language)
        say.set_folder(self.lang_dir)

    def get_database_paths(self) -> List[AbsolutePath]:
        return sorted(self.databases.keys())
