import os
from itertools import zip_longest
from typing import Iterable

from pysaurus.core import notifications
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.constants import THUMBNAIL_EXTENSION, VIDEO_SUPPORTED_EXTENSIONS
from pysaurus.core.fs_utils import correct_mtime
from pysaurus.core.informer import Information
from pysaurus.core.job_notifications import AbstractNotifier
from pysaurus.core.language import say
from pysaurus.core.modules import FNV64
from pysaurus.core.parallelization import USABLE_CPU_COUNT, parallelize
from pysaurus.core.profiling import Profiler
from pysaurus.database.algorithms.folder_scan import FolderScanner
from pysaurus.video.video_runtime_info import VideoRuntimeInfo
from pysaurus.video_raptor.video_raptor_pyav import (
    PythonVideoRaptor,
    VideoTask,
    VideoTaskResult,
)


class Videos:
    @classmethod
    def get_runtime_info_from_paths(
        cls, folders: Iterable[AbsolutePath], notifier: AbstractNotifier | None = None
    ) -> dict[AbsolutePath, VideoRuntimeInfo]:
        """Collect size/mtime/mount point of every video file under folders.

        Runs on the shared FolderScanner engine: one worker thread per mount
        point, size and mtime read from scandir entries (no extra stat call
        per file), directory links followed (so videos behind junctions stay
        indexed, as the legacy scan did).
        """
        if notifier is None:
            notifier = Information.notifier()
        paths: dict[AbsolutePath, VideoRuntimeInfo] = {}
        with Profiler(title=say("Collect videos"), notifier=notifier):
            result = FolderScanner(
                folders,
                notifier=notifier,
                extensions=VIDEO_SUPPORTED_EXTENSIONS,
                follow_links=True,
            ).scan()
            for bucket in (result.videos_indexed, result.videos_unknown):
                for files in bucket.values():
                    for info in files:
                        paths[info.path] = VideoRuntimeInfo(
                            size=info.size,
                            mtime=correct_mtime(info.mtime, info.path.path),
                            driver_id=info.driver_id,
                            is_file=True,
                        )
        notifier.notify(notifications.FinishedCollectingVideos(paths))
        return paths

    @classmethod
    def hunt(
        cls,
        filenames: list[AbsolutePath],
        need_thumbs: list[AbsolutePath],
        working_directory: str,
        runtime_info: dict[AbsolutePath, VideoRuntimeInfo] | None = None,
    ) -> list[VideoTaskResult]:
        hasher = FNV64()
        tasks = []
        filenames_without_thumbs = set(need_thumbs)
        for filename in filenames:
            tasks.append(
                VideoTask(
                    filename,
                    need_info=True,
                    thumb_path=AbsolutePath.compose(
                        working_directory, hasher(filename.path), THUMBNAIL_EXTENSION
                    ).path,
                )
            )
            filenames_without_thumbs.discard(filename)
        for filename_no_thumb in filenames_without_thumbs:
            tasks.append(
                VideoTask(
                    filename_no_thumb,
                    thumb_path=AbsolutePath.compose(
                        working_directory,
                        hasher(filename_no_thumb.path),
                        THUMBNAIL_EXTENSION,
                    ).path,
                )
            )

        if not tasks:
            return []

        tasks = cls._interleave_by_disk(tasks, runtime_info)
        notifier = Information.notifier()
        raptor = PythonVideoRaptor()
        with Profiler(say("Collect videos info"), notifier=notifier):
            results: list[VideoTaskResult] = list(
                parallelize(
                    raptor.capture,
                    tasks,
                    cpu_count=min(USABLE_CPU_COUNT, len(tasks)),
                    ordered=False,
                    notifier=notifier,
                    kind="video(s)",
                )
            )
        assert len(results) == len(filenames) + len(filenames_without_thumbs)
        return results

    @staticmethod
    def _interleave_by_disk(
        tasks: list[VideoTask],
        runtime_info: dict[AbsolutePath, VideoRuntimeInfo] | None,
    ) -> list[VideoTask]:
        """Round-robin the tasks between mount points.

        Paths arrive sorted, so all the videos of a disk are consecutive: the
        workers saturate one disk at a time while the others sit idle. Since
        the collect is I/O bound (a whole-stroke seek dominates every video),
        spreading the workers over every disk is what actually shortens it.
        """
        groups: dict[str, list[VideoTask]] = {}
        for task in tasks:
            info = runtime_info.get(task.filename) if runtime_info else None
            mount = (info.driver_id if info and info.driver_id else None) or (
                os.path.splitdrive(task.filename.path)[0]
            )
            groups.setdefault(mount, []).append(task)
        if len(groups) < 2:
            return tasks
        return [
            task
            for row in zip_longest(*groups.values())
            for task in row
            if task is not None
        ]
