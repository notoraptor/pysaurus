import logging
import multiprocessing
from typing import Iterable

from pysaurus.core.components import AbsolutePath, PathType
from pysaurus.core.notifying import DEFAULT_NOTIFIER, Notifier
from pysaurus.database.jsdb.json_database import JsonDatabase
from saurus.sql.pysaurus_collection import PysaurusCollection

logger = logging.getLogger(__name__)

USE_SQL = False
BaseDatabase = PysaurusCollection if USE_SQL else JsonDatabase


class Database(BaseDatabase):
    __slots__ = ("_initial_pid",)

    def __init__(self, path, folders=None, notifier=DEFAULT_NOTIFIER):
        # type: (PathType, Iterable[PathType], Notifier) -> None
        path = AbsolutePath.ensure(path)

        self._initial_pid = multiprocessing.current_process().pid
        logger.debug(f"Loaded database {path.title} in process {self._initial_pid}")
        assert self._initial_pid is not None

        # Load database
        super().__init__(path, folders, notifier)

    def __getattribute__(self, item):
        # TODO This method is for debugging, should be removed in production.
        attribute = super().__getattribute__(item)
        if callable(attribute):
            name = super().__getattribute__("get_name")()
            prev_pid = super().__getattribute__("_initial_pid")
            curr_pid = multiprocessing.current_process().pid
            assert prev_pid == curr_pid, (
                f"Database {name}: method {item} called in different processes "
                f"(expected {prev_pid}, got {curr_pid})"
            )
        return attribute
