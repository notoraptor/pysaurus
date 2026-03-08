"""Filesystem utilities for cross-platform filesystem type detection
and mtime correction on Windows FAT32/exFAT drives."""

import os
import sys
import time
from functools import lru_cache

_FAT_FILESYSTEMS = frozenset(("fat", "fat12", "fat16", "fat32", "vfat", "exfat"))


@lru_cache(maxsize=None)
def get_filesystem_type(root: str) -> str:
    """Return the filesystem type for the given root/mount point.

    On Windows, `root` should be a drive root like "C:\\".
    On Linux, `root` should be a mount point like "/mnt/data".

    Returns a lowercase string like "ntfs", "exfat", "ext4", etc.
    Returns "" if the filesystem type cannot be determined.
    """
    if sys.platform == "win32":
        return _get_fs_type_windows(root)
    else:
        return _get_fs_type_linux(root)


def get_path_filesystem_type(path: str) -> str:
    """Return the filesystem type for the drive/mount containing `path`."""
    if sys.platform == "win32":
        drive = os.path.splitdrive(path)[0]
        if drive:
            return get_filesystem_type(drive + "\\")
        return ""
    else:
        return get_filesystem_type(_find_mount_point(path))


def is_fat_filesystem(path: str) -> bool:
    """Return True if `path` resides on a FAT/exFAT filesystem."""
    return get_path_filesystem_type(path) in _FAT_FILESYSTEMS


def correct_mtime(mtime: float, path: str) -> float:
    """Correct a file's mtime if it resides on a FAT/exFAT drive on Windows.

    On Windows, FAT32/exFAT stores timestamps as local time without timezone.
    os.stat() converts to UTC using the *current* DST offset, which is wrong
    when DST has changed since the file was last modified.

    This function recovers the stable FAT local time, then converts it to
    correct UTC using historical DST rules via time.mktime().

    On Linux (and for NTFS on Windows), returns mtime unchanged.
    """
    if sys.platform != "win32" or not is_fat_filesystem(path):
        return mtime
    return _correct_fat_mtime(mtime)


def _correct_fat_mtime(mtime: float) -> float:
    """Apply FAT32/exFAT mtime correction on Windows.

    Formula:
        L = mtime + D_current     (recover stable FAT local time)
        T_correct = mktime(L)     (convert local time to correct UTC)
    """
    # Current UTC offset in seconds (east of UTC = positive)
    now_local = time.localtime()
    if now_local.tm_isdst and time.daylight:
        d_current = -time.altzone
    else:
        d_current = -time.timezone

    # Recover the FAT local time (this value is stable regardless of DST)
    fat_local = mtime + d_current

    # Parse into time components and let mktime determine the correct UTC
    fat_local_struct = time.gmtime(fat_local)
    corrected = time.mktime(
        time.struct_time(
            (
                fat_local_struct.tm_year,
                fat_local_struct.tm_mon,
                fat_local_struct.tm_mday,
                fat_local_struct.tm_hour,
                fat_local_struct.tm_min,
                fat_local_struct.tm_sec,
                fat_local_struct.tm_wday,
                fat_local_struct.tm_yday,
                -1,  # let mktime auto-detect DST
            )
        )
    )
    return corrected


def _get_fs_type_windows(drive_root: str) -> str:
    import ctypes

    kernel32 = ctypes.windll.kernel32
    fs_buf = ctypes.create_unicode_buffer(1024)
    vol_buf = ctypes.create_unicode_buffer(1024)
    ok = kernel32.GetVolumeInformationW(
        drive_root, vol_buf, 1024, None, None, None, fs_buf, 1024
    )
    return fs_buf.value.lower() if ok else ""


def _get_fs_type_linux(mount_point: str) -> str:
    try:
        with open("/proc/mounts") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 3 and parts[1] == mount_point:
                    return parts[2].lower()
    except OSError:
        pass
    return ""


def _find_mount_point(path: str) -> str:
    path = os.path.realpath(path)
    while not os.path.ismount(path):
        path = os.path.dirname(path)
    return path
