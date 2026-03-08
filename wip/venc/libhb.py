"""
Minimal ctypes wrapper around HandBrake's libhb (hb.dll / libhb.so).
Only exposes the functions needed to scan sources and generate queue jobs.
"""

import ctypes
import json
import os
import sys
import time

# HB_STATE constants (from libhb/handbrake/common.h)
HB_STATE_IDLE = 1
HB_STATE_SCANNING = 2
HB_STATE_SCANDONE = 4

# Size of hb_state_t is opaque; we only need the first int (state field).
# Allocate a generous buffer to cover the full struct.
_HB_STATE_BUF_SIZE = 1024

_SEARCH_PATHS = ["C:/Program Files/HandBrake", "C:/Program Files (x86)/HandBrake"]

REQUIRED_FUNCTIONS = [
    "hb_global_init",
    "hb_init",
    "hb_list_init",
    "hb_list_add",
    "hb_list_close",
    "hb_scan",
    "hb_get_state2",
    "hb_get_title_set_json",
    "hb_preset_job_init_json",
    "hb_close",
    "hb_global_close",
]


def _find_hb_dll() -> str:
    """Find hb.dll in standard HandBrake installation paths."""
    for directory in _SEARCH_PATHS:
        candidate = os.path.join(directory, "hb.dll")
        if os.path.isfile(candidate):
            return candidate
    return None


def _load_dll(dll_path: str):
    """Load hb.dll and verify all required functions are exported."""
    # Add the DLL directory so dependent DLLs (ffmpeg, x265, ...) are found
    dll_dir = os.path.dirname(dll_path)
    os.add_dll_directory(dll_dir)
    try:
        dll = ctypes.CDLL(dll_path)
    except OSError as e:
        sys.exit(f"[ERROR] Failed to load {dll_path}: {e}")

    missing = []
    for name in REQUIRED_FUNCTIONS:
        try:
            getattr(dll, name)
        except AttributeError:
            missing.append(name)

    if missing:
        sys.exit(
            f"[ERROR] hb.dll is missing required functions: {', '.join(missing)}\n"
            "        Your HandBrake version may be too old."
        )

    return dll


class LibHB:
    """High-level wrapper around libhb for scan + preset job generation."""

    def __init__(self, dll_path: str = None):
        if dll_path is None:
            dll_path = _find_hb_dll()
        if dll_path is None:
            sys.exit(
                "[ERROR] Cannot find hb.dll.\n"
                "        Make sure HandBrake is installed in a standard location,\n"
                "        or pass the path explicitly."
            )

        self._dll = _load_dll(dll_path)
        self._setup_signatures()
        self._handle = None

    def _setup_signatures(self):
        dll = self._dll

        # int hb_global_init(void)
        dll.hb_global_init.restype = ctypes.c_int
        dll.hb_global_init.argtypes = []

        # hb_handle_t * hb_init(int verbose)
        dll.hb_init.restype = ctypes.c_void_p
        dll.hb_init.argtypes = [ctypes.c_int]

        # hb_list_t * hb_list_init(void)
        dll.hb_list_init.restype = ctypes.c_void_p
        dll.hb_list_init.argtypes = []

        # void hb_list_add(hb_list_t*, void*)
        dll.hb_list_add.restype = None
        dll.hb_list_add.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        # void hb_list_close(hb_list_t**)
        dll.hb_list_close.restype = None
        dll.hb_list_close.argtypes = [ctypes.POINTER(ctypes.c_void_p)]

        # void hb_scan(hb_handle_t*, hb_list_t* paths, int title_index,
        #              int preview_count, int store_previews,
        #              uint64_t min_duration, uint64_t max_duration,
        #              int crop_threshold_frames, int crop_threshold_pixels,
        #              hb_list_t* exclude_extensions,
        #              int hw_decode, int keep_duplicate_titles)
        dll.hb_scan.restype = None
        dll.hb_scan.argtypes = [
            ctypes.c_void_p,  # handle
            ctypes.c_void_p,  # paths (hb_list_t*)
            ctypes.c_int,  # title_index
            ctypes.c_int,  # preview_count
            ctypes.c_int,  # store_previews
            ctypes.c_uint64,  # min_duration
            ctypes.c_uint64,  # max_duration
            ctypes.c_int,  # crop_threshold_frames
            ctypes.c_int,  # crop_threshold_pixels
            ctypes.c_void_p,  # exclude_extensions (hb_list_t*)
            ctypes.c_int,  # hw_decode
            ctypes.c_int,  # keep_duplicate_titles
        ]

        # void hb_get_state2(hb_handle_t*, hb_state_t*)
        dll.hb_get_state2.restype = None
        dll.hb_get_state2.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        # char * hb_get_title_set_json(hb_handle_t*)
        dll.hb_get_title_set_json.restype = ctypes.c_char_p
        dll.hb_get_title_set_json.argtypes = [ctypes.c_void_p]

        # char * hb_preset_job_init_json(hb_handle_t*, int title_index,
        #                                const char* preset)
        dll.hb_preset_job_init_json.restype = ctypes.c_char_p
        dll.hb_preset_job_init_json.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_char_p,
        ]

        # void hb_close(hb_handle_t**)
        dll.hb_close.restype = None
        dll.hb_close.argtypes = [ctypes.POINTER(ctypes.c_void_p)]

        # void hb_global_close(void)
        dll.hb_global_close.restype = None
        dll.hb_global_close.argtypes = []

    def init(self, verbose: int = 0):
        """Initialize libhb globally and create a handle."""
        self._dll.hb_global_init()
        self._handle = self._dll.hb_init(verbose)
        if not self._handle:
            sys.exit("[ERROR] hb_init() returned NULL.")

    def close(self):
        """Release the handle and global resources."""
        if self._handle:
            handle_ptr = ctypes.c_void_p(self._handle)
            self._dll.hb_close(ctypes.byref(handle_ptr))
            self._handle = None
        self._dll.hb_global_close()

    def _make_path_list(self, filepath: str):
        """Create an hb_list_t containing a single path string."""
        path_list = self._dll.hb_list_init()
        # hb_list_add expects a void* — we pass a C string (char*).
        # The string must stay alive during the scan, so we keep a reference.
        path_bytes = ctypes.c_char_p(filepath.encode("utf-8"))
        self._dll.hb_list_add(path_list, path_bytes)
        return path_list, path_bytes

    def scan(self, filepath: str, title_index: int = 0):
        """
        Scan a source file. title_index=0 scans all titles.
        Blocks until the scan is complete.
        """
        path_list, _path_ref = self._make_path_list(filepath)
        self._dll.hb_scan(
            self._handle,
            path_list,  # hb_list_t* paths
            title_index,  # title_index
            10,  # preview_count
            0,  # store_previews
            0,  # min_duration
            0,  # max_duration
            0,  # crop_threshold_frames
            0,  # crop_threshold_pixels
            None,  # exclude_extensions
            0,  # hw_decode
            0,  # keep_duplicate_titles
        )
        self._wait_for_scan()

    def _wait_for_scan(self):
        """Poll hb_get_state2 until scanning finishes."""
        state_buf = ctypes.create_string_buffer(_HB_STATE_BUF_SIZE)
        while True:
            self._dll.hb_get_state2(self._handle, state_buf)
            # First 4 bytes = int state
            state = ctypes.c_int.from_buffer_copy(state_buf[:4]).value
            if state == HB_STATE_SCANDONE:
                return
            if state not in (HB_STATE_IDLE, HB_STATE_SCANNING):
                sys.exit(f"[ERROR] Unexpected state during scan: {state}")
            time.sleep(0.1)

    def get_title_set_json(self) -> dict:
        """Get the scanned title set as a Python dict."""
        raw = self._dll.hb_get_title_set_json(self._handle)
        if not raw:
            sys.exit("[ERROR] hb_get_title_set_json() returned NULL.")
        return json.loads(raw.decode("utf-8"))

    def preset_job_init_json(self, title_index: int, preset_json: str) -> dict:
        """
        Apply a preset to a scanned title and return the resulting job dict.
        This is the core function: HandBrake's own code handles track selection,
        encoder mapping, resolution, filters, etc.
        """
        raw = self._dll.hb_preset_job_init_json(
            self._handle, title_index, preset_json.encode("utf-8")
        )
        if not raw:
            return None
        return json.loads(raw.decode("utf-8"))
