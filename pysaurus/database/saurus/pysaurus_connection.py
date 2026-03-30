import inspect
import os
from typing import Iterable

from skullite import Skullite, SkulliteFunction

from pysaurus.database.saurus import sql_functions


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
        migrations = [
            "ALTER TABLE video ADD COLUMN similarity_id_reencoded INTEGER",
            # Rename virtual column bit_rate -> byte_rate
            "ALTER TABLE video DROP COLUMN bit_rate",
            "ALTER TABLE video ADD COLUMN byte_rate DOUBLE GENERATED ALWAYS AS"
            " (IIF(duration = 0, 0, file_size *"
            " COALESCE(NULLIF(duration_time_base, 0), 1) / duration)) VIRTUAL",
            # Filename-derived virtual columns for searchexp
            "ALTER TABLE video ADD COLUMN _basename TEXT GENERATED ALWAYS AS"
            " (IIF("
            " RTRIM(REPLACE(filename, char(92), '/'), REPLACE(REPLACE(filename, char(92), '/'), '/', '')) = '',"
            " REPLACE(filename, char(92), '/'),"
            " SUBSTR(REPLACE(filename, char(92), '/'), LENGTH(RTRIM(REPLACE(filename, char(92), '/'), REPLACE(REPLACE(filename, char(92), '/'), '/', ''))) + 1)"
            " )) VIRTUAL",
            "ALTER TABLE video ADD COLUMN extension TEXT GENERATED ALWAYS AS"
            " (CASE"
            " WHEN RTRIM(_basename, REPLACE(_basename, '.', '')) = '' OR LENGTH(RTRIM(_basename, REPLACE(_basename, '.', ''))) = 1 THEN ''"
            " ELSE LOWER(SUBSTR(_basename, LENGTH(RTRIM(_basename, REPLACE(_basename, '.', ''))) + 1))"
            " END) VIRTUAL",
            "ALTER TABLE video ADD COLUMN file_title TEXT GENERATED ALWAYS AS"
            " (CASE"
            " WHEN RTRIM(_basename, REPLACE(_basename, '.', '')) = '' THEN _basename"
            " WHEN LENGTH(RTRIM(_basename, REPLACE(_basename, '.', ''))) = 1 THEN SUBSTR(_basename, 2)"
            " ELSE SUBSTR(_basename, 1, LENGTH(RTRIM(_basename, REPLACE(_basename, '.', ''))) - 1)"
            " END) VIRTUAL",
        ]
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
