import os

from pysaurus.core import constants
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.fs_utils import correct_mtime
from pysaurus.core.modules import FileSystem
from pysaurus.video.video_runtime_info import VideoRuntimeInfo


def _scan_folder_for_videos(folder: str, files: dict[AbsolutePath, VideoRuntimeInfo]):
    folder_mount_point = AbsolutePath(folder).get_mount_point()
    stack = [folder]
    while stack:
        current_folder = stack.pop()
        for entry in FileSystem.scandir(current_folder):
            if entry.is_dir():
                stack.append(entry.path)
            elif (
                os.path.splitext(entry.name)[1][1:].lower()
                in constants.VIDEO_SUPPORTED_EXTENSIONS
            ):
                entry_path = AbsolutePath(entry.path)
                stat = os.stat(entry_path.path)
                files[entry_path] = VideoRuntimeInfo(
                    size=stat.st_size,
                    mtime=correct_mtime(stat.st_mtime, entry_path.path),
                    driver_id=folder_mount_point,
                    is_file=True,
                )


def scan_path_for_videos(
    path: AbsolutePath, files: dict[AbsolutePath, VideoRuntimeInfo]
):
    if path.isdir():
        _scan_folder_for_videos(path.path, files)
    elif path.extension in constants.VIDEO_SUPPORTED_EXTENSIONS:
        stat = FileSystem.stat(path.path)
        files[path] = VideoRuntimeInfo(
            size=stat.st_size,
            mtime=correct_mtime(stat.st_mtime, path.path),
            driver_id=path.get_mount_point(),
            is_file=True,
        )
