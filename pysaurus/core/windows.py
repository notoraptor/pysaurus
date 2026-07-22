import ctypes
from ctypes import wintypes

MAX_PATH = 260  # Win32 limit, terminal NUL included: usable length is 259.

_WIN_PREFIX = "\\\\?\\"
_WIN_UNC_PREFIX = "\\\\?\\UNC\\"

_GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
_GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
_GetShortPathNameW.restype = wintypes.DWORD


def strip_win_prefix(path: str) -> str:
    """Return path without the ``\\\\?\\`` long-path prefix, if any."""
    if path.startswith(_WIN_UNC_PREFIX):
        return "\\\\" + path[len(_WIN_UNC_PREFIX) :]
    if path.startswith(_WIN_PREFIX):
        return path[len(_WIN_PREFIX) :]
    return path


def add_win_prefix(path: str) -> str:
    """Return path with the ``\\\\?\\`` long-path prefix."""
    if path.startswith(_WIN_PREFIX):
        return path
    if path.startswith("\\\\"):
        return _WIN_UNC_PREFIX + path[2:]
    return _WIN_PREFIX + path


def get_short_path_name(long_name: str) -> str | None:
    """Get a path usable by MAX_PATH-limited programs, via 8.3 short names.

    (2021/07/11) https://stackoverflow.com/a/23598461/200291

    The API call is made with the ``\\\\?\\`` prefix — required for inputs
    >= MAX_PATH — and the prefix is stripped from the result. On volumes
    without 8.3 names (exFAT, FAT32, or NTFS with 8dot3name disabled) the
    API "succeeds" by returning its input unchanged, so the result is
    validated: anything still >= MAX_PATH is unusable.

    Return None if no usable short path can be retrieved.
    """
    source = add_win_prefix(long_name)
    output_buf_size = _GetShortPathNameW(source, None, 0)
    if output_buf_size <= 0:
        return None
    output_buf = ctypes.create_unicode_buffer(output_buf_size)
    needed = _GetShortPathNameW(source, output_buf, output_buf_size)
    assert 0 < needed < output_buf_size
    short = strip_win_prefix(output_buf.value)
    if len(short) >= MAX_PATH:
        return None
    return short
