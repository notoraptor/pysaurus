from typing import List

from pysaurus.core.classes import ListView
from pysaurus.core.constants import VIDEO_BATCH_SIZE, VIDEO_THUMB_SIZE
from pysaurus.core.database import notifications
from pysaurus.core.native.video_raptor import api as video_raptor
from pysaurus.core.notification import Notifier


def job_videos_info(job):
    results = []
    file_names, job_id, notifier = job  # type: (List[str], str, Notifier)
    count_tasks = len(file_names)
    cursor = 0
    collector = video_raptor.VideoInfoCollector(VIDEO_BATCH_SIZE)
    while cursor < count_tasks:
        notifier.notify(notifications.VideoJob(job_id, cursor, count_tasks))
        results.extend(collector.collect(ListView(file_names, cursor, cursor + VIDEO_BATCH_SIZE)))
        cursor += VIDEO_BATCH_SIZE
    collector.close()
    notifier.notify(notifications.VideoJob(job_id, count_tasks, count_tasks))
    return file_names, results


def job_videos_thumbnails(job):
    results = []
    file_names, thumb_names, thumb_folder, job_id, notifier = job  # type: (list, list, str, str, Notifier)
    cursor = 0
    count_tasks = len(file_names)
    generator = video_raptor.VideoThumbnailGenerator(VIDEO_THUMB_SIZE, thumb_folder)
    while cursor < count_tasks:
        notifier.notify(notifications.ThumbnailJob(job_id, cursor, count_tasks))
        results.extend(generator.generate(ListView(file_names, cursor, cursor + VIDEO_THUMB_SIZE),
                                          ListView(thumb_names, cursor, cursor + VIDEO_THUMB_SIZE)))
        cursor += VIDEO_THUMB_SIZE
    generator.close()
    notifier.notify(notifications.ThumbnailJob(job_id, count_tasks, count_tasks))
    del generator
    return file_names, results
