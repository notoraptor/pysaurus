from typing import Collection, Dict, List

from pysaurus.core import notifications
from pysaurus.core.components import AbsolutePath
from pysaurus.core.constants import JPEG_EXTENSION
from pysaurus.core.job_notifications import notify_job_progress, notify_job_start
from pysaurus.core.modules import ImageUtils
from pysaurus.core.notifying import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.parallelization import Job, parallelize
from pysaurus.core.profiling import Profiler
from pysaurus.miniature.miniature import Miniature
from pysaurus.video.video_file_lister import scan_path_for_videos
from pysaurus.video.video_runtime_info import VideoRuntimeInfo
from saurus.language import say


def collect_videos_from_folders(job: list) -> Dict[AbsolutePath, VideoRuntimeInfo]:
    notifier: Notifier
    path, job_id, notifier = job
    files = {}  # type: Dict[AbsolutePath, VideoRuntimeInfo]
    scan_path_for_videos(path, files)
    notify_job_progress(notifier, collect_videos_from_folders, job_id, 1, 1)
    return files


def generate_video_miniatures(job: Job) -> List[Miniature]:
    notifier: Notifier = job.args[0]
    nb_videos = len(job.batch)
    miniatures = []
    for i, (file_name, thumbnail_path) in enumerate(job.batch):
        miniatures.append(
            Miniature.from_file_name(
                thumbnail_path.path, ImageUtils.DEFAULT_THUMBNAIL_SIZE, file_name.path
            )
        )
        if (i + 1) % 500 == 0:
            notify_job_progress(
                notifier, generate_video_miniatures, job.id, i + 1, nb_videos
            )
    notify_job_progress(
        notifier, generate_video_miniatures, job.id, nb_videos, nb_videos
    )
    return miniatures


def collect_video_paths(
    sources: Collection[AbsolutePath], notifier: Notifier = DEFAULT_NOTIFIER
) -> Dict[AbsolutePath, VideoRuntimeInfo]:
    paths = {}  # type: Dict[AbsolutePath, VideoRuntimeInfo]
    notify_job_start(notifier, collect_videos_from_folders, len(sources), "folders")
    jobs = [[path, i, notifier] for i, path in enumerate(sources)]
    with Profiler(
        title=say("Collect videos"),
        notifier=notifier,
    ):
        for local_result in parallelize(
            collect_videos_from_folders, jobs, ordered=False
        ):
            paths.update(local_result)
    notifier.notify(notifications.FinishedCollectingVideos(paths))
    return paths


def image_to_jpeg(input_path):
    path = AbsolutePath(input_path)
    output_path = AbsolutePath.file_path(
        path.get_directory(), path.title, JPEG_EXTENSION
    )
    ImageUtils.open_rgb_image(path.path).save(output_path.path)
    assert output_path.isfile()
    path.delete()


def compress_thumbnails_to_jpeg(job):
    path, job_id, notifier = job
    image_to_jpeg(path)
    notify_job_progress(notifier, compress_thumbnails_to_jpeg, job_id, 1, 1)
