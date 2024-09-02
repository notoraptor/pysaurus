from typing import Collection, Dict

from pysaurus.core import notifications
from pysaurus.core.components import AbsolutePath
from pysaurus.core.modules import ImageUtils
from pysaurus.core.notifying import DEFAULT_NOTIFIER, Notifier
from pysaurus.core.parallelization import parallelize
from pysaurus.core.profiling import Profiler
from pysaurus.miniature.miniature import Miniature
from pysaurus.video import VideoRuntimeInfo
from pysaurus.video.video_file_lister import scan_path_for_videos
from saurus.language import say


def collect_videos_from_folders(
    path: AbsolutePath,
) -> Dict[AbsolutePath, VideoRuntimeInfo]:
    files: Dict[AbsolutePath, VideoRuntimeInfo] = {}
    scan_path_for_videos(path, files)
    return files


def generate_video_miniature(file_name: AbsolutePath, thumb_data: bytes) -> Miniature:
    return Miniature.from_file_data(
        thumb_data, ImageUtils.THUMBNAIL_SIZE, file_name.path
    )


def collect_video_paths(
    sources: Collection[AbsolutePath], notifier: Notifier = DEFAULT_NOTIFIER
) -> Dict[AbsolutePath, VideoRuntimeInfo]:
    paths = {}  # type: Dict[AbsolutePath, VideoRuntimeInfo]
    with Profiler(title=say("Collect videos"), notifier=notifier):
        for local_result in parallelize(
            collect_videos_from_folders,
            sources,
            ordered=False,
            notifier=notifier,
            kind="folders",
        ):
            paths.update(local_result)
    notifier.notify(notifications.FinishedCollectingVideos(paths))
    return paths
