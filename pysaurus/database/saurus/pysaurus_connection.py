import inspect
import os
from typing import Iterable

from skullite import Skullite, SkulliteFunction

from pysaurus.database.saurus import sql_functions
from pysaurus.database.saurus.migrations import LATEST_VERSION, MIGRATIONS


class PysaurusConnection(Skullite):
    __slots__ = ()

    _SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "database.sql")

    def __init__(self, db_path: str | None):
        super().__init__(
            db_path, functions=self.register_pysaurus_functions(), persistent=False
        )
        self._run_schema_script()
        self._migrate()
        # Re-run after migrations to recreate triggers/indexes that may
        # have been lost during table rebuilds.  All statements use
        # IF NOT EXISTS, so this is a no-op when nothing changed.
        self._run_schema_script()

    def _run_schema_script(self) -> None:
        with open(self._SCRIPT_PATH, encoding="utf-8") as f:
            script = f.read()
        with self.connect() as connection:
            connection.script(script)

    def _migrate(self) -> None:
        """Apply versioned migrations to bring the database up to date.

        Reads the current version from the ``collection`` table, applies
        each migration in order, and updates the stored version.

        Fresh databases (no collection row) get database.sql's latest
        schema directly and skip all migrations.
        """
        version = self._get_version()
        if version is None:
            # Fresh database: schema is already at latest via database.sql.
            # Just ensure the collection row exists.
            self.insert("collection", collection_id=0, name="", version=LATEST_VERSION)
            return
        if version >= LATEST_VERSION:
            return
        for target in range(version + 1, LATEST_VERSION + 1):
            MIGRATIONS[target](self)
        self._set_version(LATEST_VERSION)

    def _get_version(self) -> int | None:
        """Read the schema version from the collection table.

        Returns ``None`` for a fresh database (no row in collection),
        or the stored version integer for an existing one.
        """
        rows = self.query_all("SELECT version FROM collection WHERE collection_id = 0")
        if not rows:
            return None
        return rows[0]["version"]

    def _set_version(self, version: int) -> None:
        self.modify(
            "UPDATE collection SET version = ? WHERE collection_id = 0", [version]
        )

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
