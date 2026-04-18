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
        if self._is_fresh_db():
            # Brand new database: schema.sql creates everything at the
            # latest version, then we record the version.
            self._run_schema_script()
            self.insert("collection", collection_id=0, name="", version=LATEST_VERSION)
        else:
            # Existing database: migrations bring the schema up to date
            # first (safe to run before schema.sql because indexes added
            # in newer versions reference columns added by migrations).
            # Then re-run schema.sql to recreate triggers/indexes that
            # may have been lost during table rebuilds.  All statements
            # use IF NOT EXISTS, so this is a no-op when nothing changed.
            self._migrate()
            self._run_schema_script()

    def _is_fresh_db(self) -> bool:
        """Return True if the database has no video table yet.

        Used to distinguish a brand-new database (schema.sql creates
        everything) from an existing one (migrations must run first).
        """
        rows = self.query_all(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='video'"
        )
        return not rows

    def _run_schema_script(self) -> None:
        with open(self._SCRIPT_PATH, encoding="utf-8") as f:
            script = f.read()
        with self.connect() as connection:
            connection.script(script)

    def _migrate(self) -> None:
        """Apply versioned migrations to bring the database up to date.

        Reads the current version from the ``collection`` table, applies
        each migration in order, and updates the stored version.

        A pre-versioning database (video table exists but no collection
        row) is bootstrapped to version 1 and receives every migration
        from m0002 onward.
        """
        version = self._get_version()
        if version is None:
            # Pre-versioning database: seed the collection row so future
            # runs skip this branch, then fall through to run migrations
            # starting from m0002.
            self.insert("collection", collection_id=0, name="", version=1)
            version = 1
        if version >= LATEST_VERSION:
            return
        for target in range(version + 1, LATEST_VERSION + 1):
            MIGRATIONS[target](self)
        self._set_version(LATEST_VERSION)

    def _get_version(self) -> int | None:
        """Read the schema version from the collection table.

        Returns ``None`` for a pre-versioning database (no row in
        collection), or the stored version integer for a versioned one.
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
