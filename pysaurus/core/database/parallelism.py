from typing import List, Tuple

from pysaurus.core import functions as utils
from pysaurus.core.classes import ListView
from pysaurus.core.components import AbsolutePath
from pysaurus.core.constants import VIDEO_BATCH_SIZE, VIDEO_THUMB_SIZE
from pysaurus.core.database import notifications
from pysaurus.core.modules import ImageUtils
from pysaurus.core.native.video_raptor import api as video_raptor
from pysaurus.core.native.video_raptor.alignment import Miniature
from pysaurus.core.notification import Notifier


def job_collect_videos_walk(job):
    # type: (list) -> List[AbsolutePath]
    files = []
    for path in job[0]:  # type: AbsolutePath
        collect_files_walk(path, files)
    return files


def job_collect_videos_listdir(job):
    # type: (list) -> List[AbsolutePath]
    files = []
    for path in job[0]:  # type: AbsolutePath
        collect_files_listdir(path, files)
    return files


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
    notifier.notify(notifications.ThumbnailJob(job_id, count_tasks, count_tasks))
    return file_names, results


def job_generate_miniatures(job):
    # type: (Tuple[list, str]) -> List[Miniature]
    thumbnails, job_id = job
    nb_videos = len(thumbnails)
    miniatures = []
    count = 0
    for file_name, thumbnail_path in thumbnails:
        miniatures.append(Miniature.from_file_name(
            thumbnail_path.path, ImageUtils.DEFAULT_THUMBNAIL_SIZE, file_name))
        count += 1
        if count % 500 == 0:
            print('[Generating miniatures on thread %s] %d/%d' % (job_id, count, nb_videos))
    print('[Generated miniatures on thread %s] %d/%d' % (job_id, count, nb_videos))
    return miniatures


def _extension(string):
    # type: (str) -> str
    index_of_dot = string.rfind('.')
    if index_of_dot > 0:
        return string[(index_of_dot + 1):].lower()
    return ''


def collect_files_listdir(input_path, files):
    # type: (AbsolutePath, List[AbsolutePath]) -> None
    if input_path.isdir():
        for file_name in input_path.listdir():
            collect_files_listdir(AbsolutePath.join(input_path, file_name), files)
    elif input_path.isfile() and input_path.extension in utils.VIDEO_SUPPORTED_EXTENSIONS:
        files.append(input_path)


def collect_files_walk(input_path, files):
    # type: (AbsolutePath, List[AbsolutePath]) -> None
    count_before = len(files)
    for folder, _, file_names in input_path.walk():
        for file_name in file_names:
            if _extension(file_name) in utils.VIDEO_SUPPORTED_EXTENSIONS:
                files.append(AbsolutePath.join(folder, file_name))
    if len(files) == count_before and input_path.isfile() and input_path.extension in utils.VIDEO_SUPPORTED_EXTENSIONS:
        files.append(input_path)
