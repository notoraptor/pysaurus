from pysaurus.core.modules import System


if System.is_windows():
    VLC_PATH = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
else:
    VLC_PATH = "vlc"
