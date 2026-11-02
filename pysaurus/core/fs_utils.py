"""Path helpers shared by AbsolutePath: Windows long-path prefixes and mount
point normalization."""

import os
import sys

# Windows long-path prefixes.
WIN_PREFIX = "\\\\?\\"
LEN_WIN_PREFIX = len(WIN_PREFIX)
WIN_UNC_PREFIX = "\\\\?\\UNC\\"


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
