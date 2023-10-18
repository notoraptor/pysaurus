import logging
import tempfile
from multiprocessing import Pool
from typing import Dict, Iterable, List

from pysaurus.application import exceptions
from pysaurus.core.components import AbsolutePath
from pysaurus.core.constants import PYTHON_ERROR_THUMBNAIL
from pysaurus.core.informer import Informer
from pysaurus.core.parallelization import run_split_batch
from pysaurus.core.profiling import Profiler
from pysaurus.database import jobs_python
from pysaurus.video import VIDEO_SCHEMA, VideoRuntimeInfo
from pysaurus.video_raptor.video_raptor_pyav import VideoRaptor as PythonVideoRaptor
from saurus.language import say
from saurus.sql.sql_old.video_entry import VideoEntry

logger = logging.getLogger(__name__)

try:
    from pysaurus.video_raptor.video_raptor_native import VideoRaptor
except exceptions.CysaurusUnavailable:
    VideoRaptor = PythonVideoRaptor
    logger.warning("Using fallback backend for videos info and thumbnails.")


class ThumbnailResult:
    __slots__ = ("video_path", "thumbnail_path", "errors")
    video_path: str
    thumbnail_path: str
    errors: List[str]

    def __init__(self, video_path, thumbnail_path=None, errors=None):
        self.video_path = video_path
        self.thumbnail_path = thumbnail_path
        self.errors = errors


class Videos:
    @classmethod
    def get_runtime_info_from_paths(
        cls, folders: Iterable[AbsolutePath]
    ) -> Dict[AbsolutePath, VideoRuntimeInfo]:
        return jobs_python.collect_video_paths(list(folders), Informer.default())

    @classmethod
    def get_info_from_filenames(cls, filenames: List[str]) -> List[VideoEntry]:
        if not filenames:
            return []

        notifier = Informer.default()
        backend_raptor = VideoRaptor()
        with tempfile.TemporaryDirectory() as working_directory:
            with Profiler(say("Collect videos info"), notifier=notifier):
                notifier.task(
                    backend_raptor.collect_video_info, len(filenames), "videos"
                )
                results = list(
                    run_split_batch(
                        backend_raptor.collect_video_info,
                        filenames,
                        extra_args=[working_directory, notifier],
                    )
                )

        new = [
            VideoEntry(
                **VIDEO_SCHEMA.ensure_long_keys(d, backend_raptor.RETURNS_SHORT_KEYS)
            )
            for arr in results
            for d in arr
        ]
        assert len(filenames) == len(new)

        return new

    @classmethod
    def get_thumbnails(
        cls, video_paths: List[AbsolutePath], working_directory: str
    ) -> Dict[str, ThumbnailResult]:
        notifier = Informer.default()
        # Generate thumbnail filenames and tasks
        tasks = [
            (
                notifier,
                i,
                filename.path,
                AbsolutePath.file_path(working_directory, i, "jpg").path,
            )
            for i, filename in enumerate(video_paths)
        ]
        # Generate thumbnail files
        expected_thumbs = {
            filename: ThumbnailResult(filename, thumb_path)
            for _, _, filename, thumb_path in tasks
        }
        raptor = PythonVideoRaptor()
        with Profiler(say("Generate thumbnail files"), notifier):
            notifier.task(raptor.run_thumbnail_task, len(tasks), "thumbnails")
            with Pool() as p:
                errors = list(p.starmap(raptor.run_thumbnail_task, tasks))
        for err in errors:
            if err:
                expected_thumbs[err["filename"]].errors = list(err["errors"]) + [
                    PYTHON_ERROR_THUMBNAIL
                ]

        return expected_thumbs
