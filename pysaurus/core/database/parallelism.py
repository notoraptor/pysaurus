from typing import List, Tuple

from pysaurus.core import functions as utils
from pysaurus.core.components import AbsolutePath
from pysaurus.core.constants import VIDEO_BATCH_SIZE
from pysaurus.core.database import notifications
from pysaurus.core.modules import ImageUtils
from pysaurus.core.native.video_raptor import api as video_raptor
from pysaurus.core.native.video_raptor.alignment import Miniature
from pysaurus.core.notification import Notifier


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


def job_generate_miniatures(job):
    # type: (Tuple[list, str]) -> List[Miniature]
    thumbnails, job_id = job
    nb_videos = len(thumbnails)
    miniatures = []
    count = 0
    for file_name, thumbnail_path in thumbnails:
        miniatures.append(Miniature.from_file_name(thumbnail_path.path, ImageUtils.DEFAULT_THUMBNAIL_SIZE, file_name))
        count += 1
        if count % 500 == 0:
            print('[Generating miniatures on thread %s] %d/%d' % (job_id, count, nb_videos))
    print('[Generated miniatures on thread %s] %d/%d' % (job_id, count, nb_videos))
    return miniatures


def collect_files(input_path, files):
    # type: (AbsolutePath, List[AbsolutePath]) -> None
    if input_path.isdir():
        for file_name in input_path.listdir():
            collect_files(AbsolutePath.join(input_path, file_name), files)
    elif input_path.isfile() and input_path.extension in utils.VIDEO_SUPPORTED_EXTENSIONS:
        files.append(input_path)
