from multiprocessing import Pool
from typing import Collection, Dict, List

from pysaurus.core import job_notifications, notifications
from pysaurus.core.components import AbsolutePath
from pysaurus.core.constants import CPU_COUNT
from pysaurus.core.job_notifications import JobNotifications
from pysaurus.core.job_utils import Job
from pysaurus.core.modules import ImageUtils
from pysaurus.core.notifier import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.profiling import Profiler
from pysaurus.database.miniature_tools.miniature import Miniature
from pysaurus.database.video_file_lister import scan_path_for_videos
from pysaurus.database.video_runtime_info import VideoRuntimeInfo
from saurus.language import say


def job_collect_videos_stats(job: list) -> Dict[AbsolutePath, VideoRuntimeInfo]:
    job_notifier: JobNotifications
    path, job_id, job_notifier = job
    files = {}  # type: Dict[AbsolutePath, VideoRuntimeInfo]
    scan_path_for_videos(path, files)
    job_notifier.progress(job_id, 1, 1)
    return files


def job_generate_miniatures(job: Job) -> List[Miniature]:
    jobn: JobNotifications = job.args[0]
    nb_videos = len(job.batch)
    miniatures = []
    for i, (file_name, thumbnail_path) in enumerate(job.batch):
        miniatures.append(
            Miniature.from_file_name(
                thumbnail_path.path, ImageUtils.DEFAULT_THUMBNAIL_SIZE, file_name.path
            )
        )
        if (i + 1) % 500 == 0:
            jobn.progress(job.id, i + 1, nb_videos)
    jobn.progress(job.id, nb_videos, nb_videos)
    return miniatures


def collect_video_paths(
    sources: Collection[AbsolutePath], notifier: Notifier = DEFAULT_NOTIFIER
) -> Dict[AbsolutePath, VideoRuntimeInfo]:
    paths = {}  # type: Dict[AbsolutePath, VideoRuntimeInfo]
    job_notifier = job_notifications.CollectVideosFromFolders(len(sources), notifier)
    jobs = [[path, i, job_notifier] for i, path in enumerate(sources)]
    with Profiler(
        title=say("Collect videos ({cpu_count} threads)", cpu_count=CPU_COUNT),
        notifier=notifier,
    ):
        with Pool(CPU_COUNT) as p:
            for local_result in p.imap_unordered(job_collect_videos_stats, jobs):
                paths.update(local_result)
    notifier.notify(notifications.FinishedCollectingVideos(paths))
    return paths
