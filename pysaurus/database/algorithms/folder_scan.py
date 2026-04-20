"""
Collect non-video file statistics for database folders.

Scans every file (video and non-video) inside the database's source folders,
classified by extension. Feeds the "db file stats" page: bulk cleanup of
orphan/junk files (thumbnails, .nfo, .torrent, .part, etc.) accumulating in
the folders managed by Pysaurus.

Parallelization: one worker thread per mount point (the scan is I/O-bound,
so threads win over processes — no pickling, shared counters are simple).
Within a mount point we stay sequential: parallel access on the same spindle
thrashes seeks on HDD and brings little on SSD.

Progress is reported as a spinner-style text notification (done / discovered,
files found) because the total folder count is unknown until the scan ends.
"""

import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Iterable

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.constants import VIDEO_SUPPORTED_EXTENSIONS
from pysaurus.core.notifications import Notification
from pysaurus.core.notifying import DEFAULT_NOTIFIER

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class FileInfo:
    path: AbsolutePath
    extension: str
    size: int


@dataclass(slots=True)
class FolderScanResult:
    videos_indexed: dict[str, list[FileInfo]] = field(default_factory=dict)
    videos_unknown: dict[str, list[FileInfo]] = field(default_factory=dict)
    others: dict[str, list[FileInfo]] = field(default_factory=dict)


class FolderScanProgress(Notification):
    __slots__ = ("folders_done", "folders_discovered", "files_found")

    def __init__(self, folders_done: int, folders_discovered: int, files_found: int):
        self.folders_done = folders_done
        self.folders_discovered = folders_discovered
        self.files_found = files_found

    def __str__(self):
        return (
            f"FolderScanProgress("
            f"{self.folders_done}/{self.folders_discovered} folders, "
            f"{self.files_found} files)"
        )


class FolderScanner:
    """Walk a set of folders, one worker thread per mount point."""

    __slots__ = ("folders", "indexed", "notifier")
    PROGRESS_INTERVAL_S = 0.2
    COUNTER_BATCH = 50

    def __init__(
        self,
        folders: Iterable[AbsolutePath],
        indexed: Iterable[AbsolutePath] = (),
        notifier=DEFAULT_NOTIFIER,
    ):
        self.folders: list[AbsolutePath] = [AbsolutePath.ensure(f) for f in folders]
        self.indexed: frozenset[AbsolutePath] = frozenset(
            AbsolutePath.ensure(p) for p in indexed
        )
        self.notifier = notifier

    def scan(self) -> FolderScanResult:
        existing = [f for f in self.folders if f.exists()]
        if not existing:
            return FolderScanResult()

        groups = self._group_by_mount(existing)
        counters = _ScanCounters(initial_discovered=len(existing))
        stop = threading.Event()
        progress_thread = threading.Thread(
            target=self._emit_progress_loop, args=(counters, stop), daemon=True
        )
        progress_thread.start()

        try:
            per_mount: list[dict[str, list[FileInfo]]] = []
            with ThreadPoolExecutor(max_workers=len(groups)) as executor:
                futures = [
                    executor.submit(self._scan_mount, seeds, counters)
                    for seeds in groups.values()
                ]
                for fut in futures:
                    per_mount.append(fut.result())
        finally:
            stop.set()
            progress_thread.join()
            self._emit_progress(counters)

        return self._classify(per_mount)

    @staticmethod
    def _group_by_mount(folders: list[AbsolutePath]) -> dict[str, list[AbsolutePath]]:
        groups: dict[str, list[AbsolutePath]] = {}
        for folder in folders:
            try:
                key = folder.get_mount_point()
            except OSError:
                key = os.path.splitdrive(folder.standard_path)[0]
            groups.setdefault(key, []).append(folder)
        return groups

    def _scan_mount(
        self, seed_folders: list[AbsolutePath], counters: "_ScanCounters"
    ) -> dict[str, list[FileInfo]]:
        by_ext: dict[str, list[FileInfo]] = {}
        stack: list[AbsolutePath] = list(seed_folders)
        local_done = local_discovered = local_files = 0
        while stack:
            current = stack.pop()
            local_done += 1
            try:
                # Use os.scandir as context manager to make sure OS folder handler is closed at end of iteration.
                with os.scandir(current.path) as iterator:
                    for entry in iterator:
                        try:
                            if entry.is_dir(follow_symlinks=False):
                                stack.append(AbsolutePath(entry.path))
                                local_discovered += 1
                            elif entry.is_file(follow_symlinks=False):
                                size = entry.stat(follow_symlinks=False).st_size
                                path = AbsolutePath(entry.path)
                                ext = path.extension
                                by_ext.setdefault(ext, []).append(
                                    FileInfo(path, ext, size)
                                )
                                local_files += 1
                        except OSError as exc:
                            logger.debug("Skipping entry %s: %s", entry.path, exc)
            except OSError as exc:
                logger.debug("Skipping folder %s: %s", current, exc)
            if local_done + local_discovered + local_files >= self.COUNTER_BATCH:
                counters.update(
                    done=local_done, discovered=local_discovered, files=local_files
                )
                local_done = local_discovered = local_files = 0
        counters.update(done=local_done, discovered=local_discovered, files=local_files)
        return by_ext

    def _emit_progress_loop(
        self, counters: "_ScanCounters", stop: threading.Event
    ) -> None:
        while not stop.wait(self.PROGRESS_INTERVAL_S):
            self._emit_progress(counters)

    def _emit_progress(self, counters: "_ScanCounters") -> None:
        done, discovered, files = counters.snapshot()
        self.notifier.notify(FolderScanProgress(done, discovered, files))

    def _classify(self, per_mount: list[dict[str, list[FileInfo]]]) -> FolderScanResult:
        result = FolderScanResult()
        for mount_result in per_mount:
            for ext, files in mount_result.items():
                if ext in VIDEO_SUPPORTED_EXTENSIONS:
                    for info in files:
                        bucket = (
                            result.videos_indexed
                            if info.path in self.indexed
                            else result.videos_unknown
                        )
                        bucket.setdefault(ext, []).append(info)
                else:
                    result.others.setdefault(ext, []).extend(files)
        return result


class _ScanCounters:
    __slots__ = ("_lock", "folders_done", "folders_discovered", "files_found")

    def __init__(self, initial_discovered: int):
        self._lock = threading.Lock()
        self.folders_done = 0
        self.folders_discovered = initial_discovered
        self.files_found = 0

    def update(self, *, done: int = 0, discovered: int = 0, files: int = 0) -> None:
        with self._lock:
            self.folders_done += done
            self.folders_discovered += discovered
            self.files_found += files

    def snapshot(self) -> tuple[int, int, int]:
        with self._lock:
            return self.folders_done, self.folders_discovered, self.files_found
