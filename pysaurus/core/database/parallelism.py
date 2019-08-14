from typing import List

from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.database import notifications
from pysaurus.core.notification import Notifier
from pysaurus.core.utils import functions as utils
from pysaurus.core.utils.constants import VIDEO_BATCH_SIZE
from pysaurus.core.video_raptor import api as video_raptor


def job_collect_videos(job):
    # type: (list) -> List[AbsolutePath]
    files = []
    for path in job[0]:  # type: AbsolutePath
        collect_files(path, files)
    return files


def job_videos_info(job):
    results = []
    file_names, job_id, notifier = job  # type: (List[str], str, Notifier)
    count_tasks = len(file_names)
    cursor = 0
    collector = video_raptor.VideoInfoCollector(VIDEO_BATCH_SIZE)
    while cursor < count_tasks:
        notifier.notify(notifications.VideoJob(job_id, cursor, count_tasks))
        results.extend(collector.collect(file_names[cursor:(cursor + VIDEO_BATCH_SIZE)]))
        cursor += VIDEO_BATCH_SIZE
    notifier.notify(notifications.VideoJob(job_id, count_tasks, count_tasks))
    return file_names, results


def job_videos_thumbnails(job):
    results = []
    file_names, thumb_names, thumb_folder, job_id, notifier = job  # type: (list, list, str, str, Notifier)
    cursor = 0
    count_tasks = len(file_names)
    generator = video_raptor.VideoThumbnailGenerator(VIDEO_BATCH_SIZE, thumb_folder)
    while cursor < count_tasks:
        notifier.notify(notifications.ThumbnailJob(job_id, cursor, count_tasks))
        results.extend(generator.generate(file_names[cursor:(cursor + VIDEO_BATCH_SIZE)],
                                          thumb_names[cursor:(cursor + VIDEO_BATCH_SIZE)]))
        cursor += VIDEO_BATCH_SIZE
    notifier.notify(notifications.ThumbnailJob(job_id, count_tasks, count_tasks))
    return file_names, results


def collect_files(input_path, files):
    # type: (AbsolutePath, List[AbsolutePath]) -> None
    if input_path.isdir():
        for file_name in input_path.listdir():
            collect_files(AbsolutePath.join(input_path, file_name), files)
    elif input_path.isfile() and input_path.extension in utils.VIDEO_SUPPORTED_EXTENSIONS:
        files.append(input_path)
