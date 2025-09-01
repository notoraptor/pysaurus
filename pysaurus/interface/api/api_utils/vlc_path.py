import os

from pysaurus.core.modules import System

if System.is_windows():
    VLC_PATH = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
else:
    VLC_PATH = "vlc"

PYTHON_HAS_RUNTIME_VLC = System.is_windows() and os.path.isfile(VLC_PATH)
