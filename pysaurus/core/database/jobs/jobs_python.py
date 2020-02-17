from typing import List, Tuple

from pysaurus.core import functions as utils
from pysaurus.core.components import AbsolutePath
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
