from pathlib import Path

from pysaurus.application.application import Config
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.custom_json_parser import parse_json
from pysaurus.core.modules import FileSystem
from saurus.language import say
from saurus.sql.pysaurus_collection import PysaurusCollection


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

    def __init__(self, home_dir=None):
        home_dir = home_dir or str(Path.home())
        self.home_dir = AbsolutePath.ensure(home_dir)
        self.app_dir = (self.home_dir / f".{self.app_name}").mkdir()
        self.dbs_dir = (self.app_dir / "databases").mkdir()
        self.databases: dict[AbsolutePath, PysaurusCollection | None] = {}
        # Load database names.
        for entry in FileSystem.scandir(self.dbs_dir.path):  # type: os.DirEntry
            if entry.is_dir():
                self.databases[AbsolutePath(entry.path)] = None
        # Load config
        self.config = Config()
        self.config_path = self.app_dir / "config.json"
        if self.config_path.exists():
            assert self.config_path.isfile()
            self.config = Config(parse_json(self.config_path))
        # TODO Load lang (not yet correctly handled)
        self.lang_dir = (self.app_dir / "lang").mkdir()
        say.set_language(self.config.language)
        say.set_folder(self.lang_dir)

    def get_database_paths(self) -> list[AbsolutePath]:
        return sorted(self.databases.keys())

    def open_database(self, name: str) -> PysaurusCollection:
        path = self.dbs_dir / name
        assert path in self.databases
        if self.databases[path] is None:
            self.databases[path] = PysaurusCollection(path)
        return self.databases[path]
