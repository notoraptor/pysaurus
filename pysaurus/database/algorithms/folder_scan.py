"""
Threaded file scan shared by the "db file stats" page and the database update.

Scans every file inside the database's source folders, classified by
extension. Two consumers:

- the "files" page: every file (video and non-video), for bulk cleanup of
  orphan/junk files (thumbnails, .nfo, .torrent, .part, etc.) accumulating
  in the folders managed by Pysaurus;
- the database update (``Videos.get_runtime_info_from_paths``): video files
  only (``extensions`` filter), with size/mtime read for free from scandir
  entries and the mount point recorded as ``driver_id``.

A source may also be a plain file path (the database accepts file sources):
it is then collected directly instead of being walked. ``follow_links``
controls whether directory links (symlinks/junctions) are walked into: the
files page keeps them out, the update follows them (legacy behavior, so
videos behind junctions stay indexed).

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

# Pseudo-extension used to report empty directories. Chosen with angle
# brackets so it cannot collide with any real filename extension (lowercased).
EMPTY_FOLDER_EXT = "<empty folder>"


@dataclass(slots=True, frozen=True)
class FileInfo:
    path: AbsolutePath
    extension: str
    size: int
    mtime: float = 0.0
    driver_id: str | None = None


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
    """Walk a set of folders, one worker thread per mount point.

    ``extensions`` restricts collection to the given (lowercase, dot-free)
    file extensions; ``None`` collects every file and empty folders.
    ``follow_links`` walks into directory links, with a cycle check.
    """

    __slots__ = ("folders", "indexed", "extensions", "follow_links", "notifier")
    PROGRESS_INTERVAL_S = 0.2
    COUNTER_BATCH = 50

    def __init__(
        self,
        folders: Iterable[AbsolutePath],
        indexed: Iterable[AbsolutePath] = (),
        notifier=DEFAULT_NOTIFIER,
        extensions: Iterable[str] | None = None,
        follow_links: bool = False,
    ):
        self.folders: list[AbsolutePath] = [AbsolutePath.ensure(f) for f in folders]
        self.indexed: frozenset[AbsolutePath] = frozenset(
            AbsolutePath.ensure(p) for p in indexed
        )
        self.extensions: frozenset[str] | None = (
            None if extensions is None else frozenset(extensions)
        )
        self.follow_links = follow_links
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
                    executor.submit(self._scan_mount, mount, seeds, counters)
                    for mount, seeds in groups.items()
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
                mount = folder.get_mount_point()
            except OSError:
                # Unavailable volume: fall back on the drive or UNC root.
                root = os.path.splitdrive(folder.standard_path)[0]
                mount = root + os.sep if root else folder.standard_path
            groups.setdefault(mount, []).append(folder)
        return groups

    def _scan_mount(
        self, mount: str, seed_folders: list[AbsolutePath], counters: "_ScanCounters"
    ) -> dict[str, list[FileInfo]]:
        by_ext: dict[str, list[FileInfo]] = {}
        follow = self.follow_links
        # Each entry carries the identities of the folders walked to reach it.
        # Cycle guard, useless (and unpaid for) unless links are followed.
        stack: list[tuple[AbsolutePath, tuple]] = [(f, ()) for f in seed_folders]
        local_done = local_discovered = local_files = 0
        while stack:
            current, ancestors = stack.pop()
            local_done += 1
            if follow:
                identity = self._identity(current)
                if identity is not None:
                    if identity in ancestors:
                        # Already inside this folder: a link points back up.
                        logger.debug("Cycle cut at %s", current)
                        continue
                    ancestors = ancestors + (identity,)
            had_entry = False
            access_ok = True
            try:
                # Use os.scandir as context manager to make sure OS folder handler is closed at end of iteration.
                with os.scandir(current.path) as iterator:
                    for entry in iterator:
                        had_entry = True
                        try:
                            if entry.is_dir(follow_symlinks=follow):
                                stack.append((AbsolutePath(entry.path), ancestors))
                                local_discovered += 1
                            elif entry.is_file(follow_symlinks=follow):
                                path = AbsolutePath(entry.path)
                                ext = path.extension
                                if (
                                    self.extensions is not None
                                    and ext not in self.extensions
                                ):
                                    continue
                                stat = entry.stat(follow_symlinks=follow)
                                by_ext.setdefault(ext, []).append(
                                    FileInfo(
                                        path, ext, stat.st_size, stat.st_mtime, mount
                                    )
                                )
                                local_files += 1
                        except OSError as exc:
                            logger.debug("Skipping entry %s: %s", entry.path, exc)
            except NotADirectoryError:
                # A database source may be a plain file path: collect it
                # directly. Only seeds can be files (the walk itself only
                # stacks directories). Never reported as an empty folder.
                access_ok = False
                info = self._collect_file(current, mount)
                if info is not None:
                    by_ext.setdefault(info.extension, []).append(info)
                    local_files += 1
            except OSError as exc:
                logger.debug("Skipping folder %s: %s", current, exc)
                access_ok = False
            # Report an accessible directory with no entry (neither files nor
            # subdirs) as an empty folder. Useful for bulk cleanup: a physically
            # empty folder is a typical leftover after files were removed.
            if access_ok and not had_entry and self.extensions is None:
                by_ext.setdefault(EMPTY_FOLDER_EXT, []).append(
                    FileInfo(current, EMPTY_FOLDER_EXT, 0, 0.0, mount)
                )
            if local_done + local_discovered + local_files >= self.COUNTER_BATCH:
                counters.update(
                    done=local_done, discovered=local_discovered, files=local_files
                )
                local_done = local_discovered = local_files = 0
        counters.update(done=local_done, discovered=local_discovered, files=local_files)
        return by_ext

    @staticmethod
    def _identity(path: AbsolutePath) -> tuple[int, int] | None:
        """Identify a folder, or None when it cannot be identified.

        Compared against the folders walked to reach this one, never against
        everything seen so far: a junction and its target are the same folder,
        but reaching a file through both is two legitimate paths, and the
        database indexes paths. Only re-entering a folder one is already inside
        is a cycle.

        Needs a real stat(): DirEntry.stat() gives no st_dev/st_ino on Windows.
        Filesystems reporting no inode (some network shares) opt out.
        """
        try:
            stat = os.stat(path.path)
        except OSError:
            return None  # let the walk fail and log where it normally does
        return (stat.st_dev, stat.st_ino) if stat.st_ino else None

    def _collect_file(self, path: AbsolutePath, mount: str) -> FileInfo | None:
        """Collect a source that is a plain file, honoring the extension filter."""
        ext = path.extension
        if self.extensions is not None and ext not in self.extensions:
            return None
        try:
            stat = os.stat(path.path)
        except OSError as exc:
            logger.debug("Skipping file %s: %s", path, exc)
            return None
        return FileInfo(path, ext, stat.st_size, stat.st_mtime, mount)

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
