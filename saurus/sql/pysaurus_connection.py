import inspect
import os

from saurus.sql import sql_functions
from saurus.sql.saurus_sqlite_connection import SaurusSQLiteConnection


class PysaurusConnection(SaurusSQLiteConnection):
    __slots__ = ()

    def __init__(self, db_path: str):
        super().__init__(
            os.path.join(os.path.dirname(__file__), "database.sql"), db_path
        )
        for name, function in inspect.getmembers(
            sql_functions,
            lambda value: callable(value) and value.__name__.startswith("pysaurus_"),
        ):
            signature = inspect.signature(function)
            narg = len(signature.parameters)
            self.connection.create_function(name, narg, function, deterministic=True)
