from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.database import notifications
from pysaurus.core.notification import Notifier
from pysaurus.core.utils import functions as utils
from pysaurus.core.utils.constants import VIDEO_BATCH_SIZE
from pysaurus.core.video_raptor import api as video_raptor


def job_collect_videos(job):
    # type: (list) -> dict
    folder_to_files = {}
    paths, _, notifier = job
    for path in paths:  # type: AbsolutePath
        if not path.exists():
            notifier.notify(notifications.FolderNotFound(path))
        elif path.isdir():
            collect_files(path, folder_to_files, notifier)
        elif path.extension in utils.VIDEO_SUPPORTED_EXTENSIONS:
            notifier.notify(notifications.CollectingFiles(path))
            folder_to_files.setdefault(path.get_directory(), []).append(path)
        else:
            notifier.notify(notifications.PathIgnored(path))
    return folder_to_files


def job_videos_info(job):
    results = []
    file_names, job_id, notifier = job  # type: (list, str, Notifier)
    count_tasks = len(file_names)
    cursor = 0
    while cursor < count_tasks:
        notifier.notify(notifications.VideoJob(job_id, cursor, count_tasks))
        results.extend(video_raptor.collect_video_info(file_names[cursor:(cursor + VIDEO_BATCH_SIZE)]))
        cursor += VIDEO_BATCH_SIZE
    notifier.notify(notifications.VideoJob(job_id, count_tasks, count_tasks))
    return file_names, results


def job_videos_thumbnails(job):
    results = []
    file_names, thumb_names, thumb_folder, job_id, notifier = job  # type: (list, list, str, str, Notifier)
    cursor = 0
    count_tasks = len(file_names)
    while cursor < count_tasks:
        notifier.notify(notifications.ThumbnailJob(job_id, cursor, count_tasks))
        results.extend(
            video_raptor.generate_video_thumbnails(
                file_names[cursor:(cursor + VIDEO_BATCH_SIZE)],
                thumb_names[cursor:(cursor + VIDEO_BATCH_SIZE)],
                thumb_folder))
        cursor += VIDEO_BATCH_SIZE
    notifier.notify(notifications.ThumbnailJob(job_id, count_tasks, count_tasks))
    return file_names, results


def collect_files(folder_path, folder_to_files, notifier):
    # type: (AbsolutePath, dict, Notifier) -> None
    notifier.notify(notifications.CollectingFiles(folder_path))
    for file_name in folder_path.listdir():
        path = AbsolutePath.join(folder_path, file_name)
        if path.isdir():
            collect_files(path, folder_to_files, notifier)
        elif path.extension in utils.VIDEO_SUPPORTED_EXTENSIONS:
            folder_to_files.setdefault(folder_path, []).append(path)
