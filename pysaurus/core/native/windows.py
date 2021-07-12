import ctypes
from ctypes import wintypes
_GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
_GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
_GetShortPathNameW.restype = wintypes.DWORD


def get_short_path_name(long_name: str):
    """
    Gets the short path name of a given long path.
    (2021/07/11) http://stackoverflow.com/a/23598461/200291
    """
    output_buf_size = _GetShortPathNameW(long_name, None, 0)
    assert output_buf_size > 0
    output_buf = ctypes.create_unicode_buffer(output_buf_size)
    needed = _GetShortPathNameW(long_name, output_buf, output_buf_size)
    assert 0 < needed < output_buf_size
    return output_buf.value
