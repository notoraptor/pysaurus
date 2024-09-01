from typing import Collection, Dict, List

from pysaurus.core import notifications
from pysaurus.core.abstract_notifier import AbstractNotifier
from pysaurus.core.components import AbsolutePath
from pysaurus.core.modules import ImageUtils
from pysaurus.core.notifying import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.parallelization import Job, parallelize
from pysaurus.core.profiling import Profiler
from pysaurus.miniature.miniature import Miniature
from pysaurus.video import VideoRuntimeInfo
from pysaurus.video.video_file_lister import scan_path_for_videos
from saurus.language import say


def collect_videos_from_folders(job: list) -> Dict[AbsolutePath, VideoRuntimeInfo]:
    notifier: AbstractNotifier
    path, job_id, notifier = job
    files = {}  # type: Dict[AbsolutePath, VideoRuntimeInfo]
    scan_path_for_videos(path, files)
    notifier.progress(collect_videos_from_folders, 1, 1, job_id)
    return files


def generate_video_miniatures(job: Job) -> List[Miniature]:
    notifier: AbstractNotifier = job.args[0]
    nb_videos = len(job.batch)
    miniatures = []
    for i, (file_name, thumb_data) in enumerate(job.batch):
        miniatures.append(
            Miniature.from_file_data(
                thumb_data, ImageUtils.THUMBNAIL_SIZE, file_name.path
            )
        )
        if (i + 1) % 500 == 0:
            notifier.progress(generate_video_miniatures, i + 1, nb_videos, job.id)
    notifier.progress(generate_video_miniatures, nb_videos, nb_videos, job.id)
    return miniatures


def collect_video_paths(
    sources: Collection[AbsolutePath], notifier: Notifier = DEFAULT_NOTIFIER
) -> Dict[AbsolutePath, VideoRuntimeInfo]:
    paths = {}  # type: Dict[AbsolutePath, VideoRuntimeInfo]
    jobs = [[path, i, notifier] for i, path in enumerate(sources)]
    with Profiler(title=say("Collect videos"), notifier=notifier):
        notifier.task(collect_videos_from_folders, len(sources), "folders")
        for local_result in parallelize(
            collect_videos_from_folders, jobs, ordered=False
        ):
            paths.update(local_result)
    notifier.notify(notifications.FinishedCollectingVideos(paths))
    return paths
