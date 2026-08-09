"""Ouvre séquentiellement chaque base Pysaurus pour y appliquer les migrations.

Chaque base est d'abord inspectée en lecture seule : version stockée, nombre de
chemins dont le point de montage n'est pas normalisé, et fichiers stockés sous
plusieurs graphies de ce point de montage. La migration m0006 refuse de
s'exécuter sur un tel conflit et ne signale que le premier ; ici ils sont tous
listés, et la base est laissée de côté.

Usage :
    uv run -m pysaurus.scripts.migrate_databases [HOME...] [--dry-run]

HOME est un dossier maison contenant `.Pysaurus/databases` (défaut : celui de
l'utilisateur). Exemple, pour les bases de test : `tests/home_dir_test`.
"""

import argparse
import sqlite3
import sys
from pathlib import Path

from pysaurus.core.fs_utils import normalize_mount_point
from pysaurus.database.saurus.migrations import LATEST_VERSION
from pysaurus.database.saurus.pysaurus_connection import PysaurusConnection

DB_BASENAME = "sql_path.full.db"


class ReadOnlyView:
    """Connexion en lecture seule, réduite au `query_all` dont l'inspection a besoin."""

    __slots__ = ("connection",)

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def query_all(self, query, parameters=()) -> list[sqlite3.Row]:
        return self.connection.execute(query, parameters).fetchall()


def find_databases(home: Path) -> list[Path]:
    dbs_dir = home / ".Pysaurus" / "databases"
    if not dbs_dir.is_dir():
        return []
    return sorted(
        folder / DB_BASENAME
        for folder in dbs_dir.iterdir()
        if folder.is_dir()
        and not folder.name.startswith(".")
        and (folder / DB_BASENAME).is_file()
    )


def find_filename_conflicts(filenames: list[str]) -> list[list[str]]:
    """Groupes de filenames qui ne diffèrent que par leur point de montage."""
    grouped: dict[str, list[str]] = {}
    for filename in filenames:
        grouped.setdefault(normalize_mount_point(filename), []).append(filename)
    return [sorted(names) for names in grouped.values() if len(names) > 1]


def inspect(db_path: Path) -> tuple[int | None, int, list[list[str]]]:
    """Version, chemins à normaliser et conflits, sans écrire dans la base."""
    connection = sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True)
    try:
        connection.row_factory = sqlite3.Row
        view = ReadOnlyView(connection)
        # Ligne absente : base antérieure au versionnage, que _migrate amorce.
        rows = view.query_all("SELECT version FROM collection WHERE collection_id = 0")
        version = rows[0]["version"] if rows else None
        filenames = [
            row["filename"] for row in view.query_all("SELECT filename FROM video")
        ]
        pending = sum(1 for name in filenames if normalize_mount_point(name) != name)
        return version, pending, find_filename_conflicts(filenames)
    finally:
        connection.close()


def report(
    db_path: Path, version: int | None, pending: int, conflicts: list[list[str]]
) -> None:
    shown = "pré-versionnage" if version is None else f"version {version}"
    print(f"\n== {db_path.parent}")
    print(f"   {shown}, {pending} chemin(s) à normaliser, {len(conflicts)} conflit(s)")
    for names in conflicts:
        print("   conflit : " + " <-> ".join(names))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("homes", nargs="*", help="dossiers maison à parcourir")
    parser.add_argument("--dry-run", action="store_true", help="inspecter sans migrer")
    args = parser.parse_args()

    # resolve() : as_uri() refuse un chemin relatif.
    homes = [Path(home).expanduser().resolve() for home in args.homes] or [Path.home()]
    databases = [db for home in homes for db in find_databases(home)]
    if not databases:
        print("Aucune base trouvée.")
        return 1
    print(f"{len(databases)} base(s), version cible {LATEST_VERSION}.")

    total_conflicts = 0
    for db_path in databases:
        version, pending, conflicts = inspect(db_path)
        report(db_path, version, pending, conflicts)
        total_conflicts += len(conflicts)
        if args.dry_run:
            continue
        if conflicts:
            print("   -> laissée de côté : la migration refuserait de s'exécuter")
            continue
        # Ouvrir suffit : le constructeur applique les migrations en attente.
        print(
            f"   -> ouverte, version {PysaurusConnection(str(db_path)).get_version()}"
        )

    print(f"\nTotal : {total_conflicts} conflit(s) de filename.")
    return 1 if total_conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
