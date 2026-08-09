"""Filesystem utilities for cross-platform filesystem type detection
and mtime correction on Windows FAT32/exFAT drives."""

import ctypes
import os
import sys
import time
from functools import lru_cache

_FAT_FILESYSTEMS = frozenset(("fat", "fat12", "fat16", "fat32", "vfat", "exfat"))

# Windows long-path prefixes.
WIN_PREFIX = "\\\\?\\"
LEN_WIN_PREFIX = len(WIN_PREFIX)
WIN_UNC_PREFIX = "\\\\?\\UNC\\"


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


def strip_win_prefix(path: str) -> str:
    """Return path without the ``\\\\?\\`` long-path prefix, if any."""
    if path.startswith(WIN_UNC_PREFIX):
        return "\\\\" + path[len(WIN_UNC_PREFIX) :]
    if path.startswith(WIN_PREFIX):
        return path[LEN_WIN_PREFIX:]
    return path


def add_win_prefix(path: str) -> str:
    """Return path with the ``\\\\?\\`` long-path prefix."""
    if path.startswith(WIN_PREFIX):
        return path
    if path.startswith("\\\\"):
        return WIN_UNC_PREFIX + path[2:]
    return WIN_PREFIX + path


def normalize_mount_point(path: str) -> str:
    """Fold the case of a path's mount point, leaving the rest untouched.

    No-op on POSIX, where splitdrive finds no prefix and case is significant.
    Windows spells a drive either way, and it is the one path component never
    read back from the filesystem, so it is the one that needs normalizing.

    A drive letter is uppercased, matching how Windows displays it everywhere:
    these paths reach the user (the "disk" grouping shows the mount point as
    is). A server and share keep normcase's lowercase instead -- an uppercased
    share name would look wrong, and the two families never mix.

    Called on every AbsolutePath, hence the shortcuts: splitdrive, normcase and
    the concatenation together cost more than os.path.abspath itself. The bare
    "X:" shape is tested first so the common case never pays for the others.
    """
    if sys.platform != "win32":
        # A colon is an ordinary filename character elsewhere: "a:b" is a file,
        # not a drive, and the shortcuts below would rewrite it.
        return path
    if len(path) > 1 and path[1] == ":":
        letter = path[0]
        return path if letter.isupper() else letter.upper() + path[1:]
    if (
        len(path) > LEN_WIN_PREFIX + 1
        and path[LEN_WIN_PREFIX + 1] == ":"
        and path.startswith(WIN_PREFIX)
    ):
        letter = path[LEN_WIN_PREFIX]
        return (
            path
            if letter.isupper()
            else path[:LEN_WIN_PREFIX] + letter.upper() + path[(LEN_WIN_PREFIX + 1) :]
        )
    if path[: len(WIN_UNC_PREFIX)].upper() == WIN_UNC_PREFIX:
        # Fold the server and share, but write the marker back as-is: it is a
        # prefix strip_win_prefix matches literally, not part of the mount point.
        drive, rest = os.path.splitdrive(path)
        folded = WIN_UNC_PREFIX + os.path.normcase(drive[len(WIN_UNC_PREFIX) :])
        return path if folded == drive else folded + rest
    drive, rest = os.path.splitdrive(path)
    if not drive:
        return path
    lowered = os.path.normcase(drive)
    return path if lowered == drive else lowered + rest


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
