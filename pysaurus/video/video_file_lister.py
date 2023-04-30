import os
from typing import Dict

from pysaurus.core import constants
from pysaurus.core.components import AbsolutePath
from pysaurus.core.modules import FileSystem
from pysaurus.video import VideoRuntimeInfo


def _scan_folder_for_videos(folder: str, files: Dict[AbsolutePath, VideoRuntimeInfo]):
    entry: os.DirEntry
    for entry in FileSystem.scandir(folder):
        if entry.is_dir():
            _scan_folder_for_videos(entry.path, files)
        elif (
            os.path.splitext(entry.name)[1][1:].lower()
            in constants.VIDEO_SUPPORTED_EXTENSIONS
        ):
            # NB: entry.stat()'s field st_dev is set to 0 on Windows.
            # So, we should better use os.stat().
            # Reference (2023/04/29, python 3.8):
            # https://docs.python.org/3/library/os.html#os.DirEntry.stat
            stat = os.stat(entry.path)
            files[AbsolutePath(entry.path)] = VideoRuntimeInfo.from_keys(
                size=stat.st_size,
                mtime=stat.st_mtime,
                driver_id=stat.st_dev,
                is_file=True,
            )


def scan_path_for_videos(
    path: AbsolutePath, files: Dict[AbsolutePath, VideoRuntimeInfo]
):
    if path.isdir():
        _scan_folder_for_videos(path.path, files)
    elif path.extension in constants.VIDEO_SUPPORTED_EXTENSIONS:
        stat = FileSystem.stat(path.path)
        files[path] = VideoRuntimeInfo.from_keys(
            size=stat.st_size,
            mtime=stat.st_mtime,
            driver_id=stat.st_dev,
            is_file=True,
        )
