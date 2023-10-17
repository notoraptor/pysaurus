import logging
import tempfile
from typing import Dict, Iterable, List

from pysaurus.application import exceptions
from pysaurus.core.components import AbsolutePath
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
