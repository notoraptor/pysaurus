"""Inventaire CLI des fichiers des dossiers d'une base Pysaurus.

Réutilise `FolderScanner` (voir `pysaurus/database/algorithms/folder_scan.py`),
le même moteur que la page PySide6 "Files". Affiche, par catégorie (vidéos
indexées / vidéos inconnues / autres), le nombre de fichiers et la taille
totale par extension, trié par taille décroissante.

Usage :
    uv run -m pysaurus.scripts.diagnose_db_folders <database_name>
"""

import sys

from strarr import strarr
from tqdm import tqdm

from pysaurus.application.application import Application
from pysaurus.core.file_size import FileSize
from pysaurus.core.job_notifications import AbstractNotifier
from pysaurus.database.algorithms.folder_scan import (
    FolderScanner,
    FolderScanProgress,
    FolderScanResult,
)


class TqdmNotifier(AbstractNotifier):
    """Traduit les FolderScanProgress en barre tqdm."""

    __slots__ = ("pbar",)

    def __init__(self):
        self.pbar = tqdm(desc="folders", total=0)

    def notify(self, notification):
        if isinstance(notification, FolderScanProgress):
            self.pbar.total = max(notification.folders_discovered, 1)
            self.pbar.n = notification.folders_done
            self.pbar.set_postfix(files=notification.files_found)
            self.pbar.refresh()

    def close(self):
        self.pbar.close()


def main():
    if len(sys.argv) < 2:
        print("Database name expected")
        sys.exit(1)
    database_name = sys.argv[1]
    app = Application()
    if database_name not in app.get_database_names():
        print("Database not found")
        sys.exit(1)
    database = app.open_database_from_name(database_name, update=False)

    folders = list(database.get_folders())
    indexed = {row.filename for row in database.get_videos(include=["filename"])}

    notifier = TqdmNotifier()
    try:
        result: FolderScanResult = FolderScanner(
            folders, indexed, notifier=notifier
        ).scan()
    finally:
        notifier.close()

    _print_section("VIDEOS (INDEXED)", result.videos_indexed)
    _print_section("VIDEOS (UNKNOWN)", result.videos_unknown)
    _print_section("OTHERS", result.others)


def _print_section(title, by_ext):
    if not by_ext:
        return
    print(title)
    print(strarr(_format_bucket(by_ext)))


def _format_bucket(by_ext):
    rows = [
        (ext, len(infos), sum(i.size for i in infos)) for ext, infos in by_ext.items()
    ]
    rows.sort(key=lambda t: (-t[2], t[0]))
    return [
        dict(extension=ext or "(none)", count=c, size=FileSize(s)) for ext, c, s in rows
    ]


if __name__ == "__main__":
    main()
