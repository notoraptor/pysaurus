from typing import Dict, List

from pysaurus.core.components import AbsolutePath
from pysaurus.core.job_notifications import JobNotifications
from pysaurus.core.modules import ImageUtils
from pysaurus.database.miniature_tools.miniature import Miniature
from pysaurus.database.video_file_lister import scan_path_for_videos
from pysaurus.database.video_runtime_info import VideoRuntimeInfo


def job_collect_videos_stats(job: list) -> Dict[AbsolutePath, VideoRuntimeInfo]:
    job_notifier: JobNotifications
    path, job_id, job_notifier = job
    files = {}  # type: Dict[AbsolutePath, VideoRuntimeInfo]
    scan_path_for_videos(path, files)
    job_notifier.progress(job_id, 1, 1)
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
