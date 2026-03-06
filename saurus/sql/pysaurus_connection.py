import inspect
import os
from typing import Iterable

from skullite import Skullite, SkulliteFunction

from saurus.sql import sql_functions


class PysaurusConnection(Skullite):
    __slots__ = ()

    _SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "database.sql")

    def __init__(self, db_path: str | None):
        super().__init__(
            db_path, functions=self.register_pysaurus_functions(), persistent=False
        )
        self._migrate()
        with open(self._SCRIPT_PATH, encoding="utf-8") as f:
            script = f.read()
        with self.connect() as connection:
            connection.script(script)

    def _migrate(self):
        """Apply migrations before the schema script runs.

        Runs ALTER TABLE statements for columns added after initial release.
        Must run before database.sql so that CREATE INDEX statements
        in the script can reference the new columns.
        """
        migrations = ["ALTER TABLE video ADD COLUMN similarity_id_reencoded INTEGER"]
        for sql in migrations:
            try:
                with self.connect() as connection:
                    connection.modify(sql)
            except Exception:
                pass  # Table doesn't exist yet, or column already exists

    @classmethod
    def register_pysaurus_functions(cls) -> Iterable[SkulliteFunction]:
        for name, function in inspect.getmembers(
            sql_functions,
            lambda value: callable(value) and value.__name__.startswith("pysaurus_"),
        ):
            signature = inspect.signature(function)
            narg = len(signature.parameters)
            yield SkulliteFunction(
                name=name, function=function, nb_args=narg, deterministic=True
            )
