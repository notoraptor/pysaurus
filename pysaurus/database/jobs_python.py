import os
from typing import List, Dict

from pysaurus.core import functions, constants
from pysaurus.core.components import AbsolutePath
from pysaurus.core.modules import FileSystem, ImageUtils
from pysaurus.core.notifications import JobNotifications
from pysaurus.database.miniature_tools.miniature import Miniature
from pysaurus.database.video_runtime_info import VideoRuntimeInfo


def _collect_videos_info(folder: str, files: Dict[AbsolutePath, VideoRuntimeInfo]):
    entry: os.DirEntry
    for entry in FileSystem.scandir(folder):
        if entry.is_dir():
            _collect_videos_info(entry.path, files)
        elif (
            functions.get_file_extension(entry.name)
            in constants.VIDEO_SUPPORTED_EXTENSIONS
        ):
            stat = entry.stat()
            files[AbsolutePath(entry.path)] = VideoRuntimeInfo(
                size=stat.st_size,
                mtime=stat.st_mtime,
                driver_id=stat.st_dev,
                is_file=True,
            )


def job_collect_videos_info(job: list) -> Dict[AbsolutePath, VideoRuntimeInfo]:
    jobn: JobNotifications
    paths, job_id, jobn = job
    files = {}  # type: Dict[AbsolutePath, VideoRuntimeInfo]
    for i, path in enumerate(paths):  # type: (int, AbsolutePath)
        if path.isdir():
            _collect_videos_info(path.path, files)
        elif path.extension in constants.VIDEO_SUPPORTED_EXTENSIONS:
            stat = FileSystem.stat(path.path)
            files[path] = VideoRuntimeInfo(
                size=stat.st_size,
                mtime=stat.st_mtime,
                driver_id=stat.st_dev,
                is_file=True,
            )
        jobn.progress(job_id, i, len(paths))
    jobn.progress(job_id, len(paths), len(paths))
    return files


def job_generate_miniatures(job) -> List[Miniature]:
    jobn: JobNotifications
    thumbnails, job_id, jobn = job
    nb_videos = len(thumbnails)
    miniatures = []
    for i, (file_name, thumbnail_path) in enumerate(thumbnails):
        miniatures.append(
            Miniature.from_file_name(
                thumbnail_path.path, ImageUtils.DEFAULT_THUMBNAIL_SIZE, file_name.path
            )
        )
        if (i + 1) % 500 == 0:
            jobn.progress(job_id, i + 1, nb_videos)
    jobn.progress(job_id, nb_videos, nb_videos)
    return miniatures
