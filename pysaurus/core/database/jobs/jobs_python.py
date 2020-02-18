import subprocess
from typing import List, Tuple

from pysaurus.core import functions as utils
from pysaurus.core.components import AbsolutePath
from pysaurus.core.database import notifications
from pysaurus.core.functions import get_file_extension
from pysaurus.core.modules import ImageUtils
from pysaurus.core.native.video_raptor.miniature import Miniature


def job_collect_videos(job):
    # type: (list) -> List[AbsolutePath]
    files = []
    for path in job[0]:  # type: AbsolutePath
        count_before = len(files)
        for folder, _, file_names in path.walk():
            for file_name in file_names:
                if get_file_extension(file_name) in utils.VIDEO_SUPPORTED_EXTENSIONS:
                    files.append(AbsolutePath.join(folder, file_name))
        if (len(files) == count_before
                and path.isfile()
                and path.extension in utils.VIDEO_SUPPORTED_EXTENSIONS):
            files.append(path)
    return files


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


def job_video_to_json(job):
    input_file_name, output_file_name, job_count, job_id, notifier = job

    nb_read = 0
    nb_loaded = 0
    input_file_path = AbsolutePath.ensure(input_file_name)
    output_file_path = AbsolutePath.ensure(output_file_name)
    assert input_file_path.isfile()
    if output_file_path.exists():
        output_file_path.delete()

    process = subprocess.Popen(['runVideoRaptorBatch', input_file_name, output_file_name],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in process.stdout.readlines():
        line = line.decode().strip()
        if line:
            if line.startswith('#'):
                if line.startswith('#count '):
                    nb_read = int(line[7:])
                elif line.startswith('#loaded '):
                    nb_loaded = int(line[8:])
            else:
                step = int(line)
                notifier.notify(notifications.VideoJob(job_id, step, job_count))
    program_errors = process.stderr.read().decode().strip()
    if program_errors:
        raise Exception('Video-to-JSON error: ' + program_errors)
    assert nb_read == job_count
    notifier.notify(notifications.VideoJob(job_id, job_count, job_count))
    return nb_loaded
