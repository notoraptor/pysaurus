from typing import Dict, Iterable, List

from pysaurus.core import notifications
from pysaurus.core.components import AbsolutePath
from pysaurus.core.informer import Informer
from pysaurus.core.modules import FNV64
from pysaurus.core.parallelization import parallelize
from pysaurus.core.profiling import Profiler
from pysaurus.video import VideoRuntimeInfo
from pysaurus.video.video_file_lister import scan_path_for_videos
from pysaurus.video_raptor.video_raptor_pyav import (
    PythonVideoRaptor,
    VideoTask,
    VideoTaskResult,
)
from saurus.language import say


class Videos:
    @classmethod
    def get_runtime_info_from_paths(
        cls, folders: Iterable[AbsolutePath]
    ) -> Dict[AbsolutePath, VideoRuntimeInfo]:
        sources = list(folders)
        notifier = Informer.default()
        paths = {}  # type: Dict[AbsolutePath, VideoRuntimeInfo]
        with Profiler(title=say("Collect videos"), notifier=notifier):
            for local_result in parallelize(
                cls._collect_videos_from_folders,
                sources,
                ordered=False,
                notifier=notifier,
                kind="folders",
            ):
                paths.update(local_result)
        notifier.notify(notifications.FinishedCollectingVideos(paths))
        return paths

    @classmethod
    def _collect_videos_from_folders(
        cls, path: AbsolutePath
    ) -> Dict[AbsolutePath, VideoRuntimeInfo]:
        files: Dict[AbsolutePath, VideoRuntimeInfo] = {}
        scan_path_for_videos(path, files)
        return files

    @classmethod
    def hunt(
        cls,
        filenames: List[AbsolutePath],
        need_thumbs: List[AbsolutePath],
        working_directory: str,
    ) -> List[VideoTaskResult]:
        hasher = FNV64()
        tasks = []
        filenames_without_thumbs = set(need_thumbs)
        for filename in filenames:
            tasks.append(
                VideoTask(
                    filename,
                    need_info=True,
                    thumb_path=AbsolutePath.file_path(
                        working_directory, hasher(filename.path), "jpg"
                    ).path,
                )
            )
            filenames_without_thumbs.discard(filename)
        for filename_no_thumb in filenames_without_thumbs:
            tasks.append(
                VideoTask(
                    filename_no_thumb,
                    thumb_path=AbsolutePath.file_path(
                        working_directory, hasher(filename_no_thumb.path), "jpg"
                    ).path,
                )
            )

        if not tasks:
            return []

        notifier = Informer.default()
        raptor = PythonVideoRaptor()
        with Profiler(say("Collect videos info"), notifier=notifier):
            results: List[VideoTaskResult] = list(
                parallelize(
                    raptor.capture,
                    tasks,
                    ordered=False,
                    notifier=notifier,
                    kind="video(s)",
                )
            )
        assert len(results) == len(filenames) + len(filenames_without_thumbs)
        return results
