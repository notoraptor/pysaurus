import logging
from typing import Any, Iterable, List, Tuple

from PIL.Image import Image

from other.imgsimsearch.abstract_image_provider import AbstractImageProvider
from other.imgsimsearch.approximate_comparator_annoy import ApproximateComparatorAnnoy

# from other.imgsimsearch.native_fine_comparator import compare_miniatures_native
from other.imgsimsearch.python_fine_comparator import (
    compare_miniatures as compare_miniatures_native,
)
from pysaurus.application import exceptions
from pysaurus.core.fraction import Fraction
from pysaurus.core.modules import ImageUtils
from pysaurus.core.profiling import Profiler
from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.miniature.miniature import Miniature

# from collections import deque
logger = logging.getLogger(__name__)

try:
    from pysaurus.video_similarities.alignment_raptor import alignment as backend_sim

    has_cpp = True
except exceptions.CysaurusUnavailable:
    from pysaurus.video_similarities import backend_python as backend_sim

    has_cpp = False
    logger.warning("Using fallback backend for video similarities search.")

FRAC_SIM_LIMIT = Fraction(88, 100)
SIM_LIMIT = float(FRAC_SIM_LIMIT)


class DbImageProvider(AbstractImageProvider):
    __slots__ = ("videos",)

    def __init__(self, db: AbstractDatabase):
        self.videos = {
            video["filename"].path: video
            for video in db.get_videos(
                include=[
                    "video_id",
                    "filename",
                    "thumbnail_blob",
                    "duration",
                    "duration_time_base",
                ],
                where={"readable": True, "with_thumbnails": True},
            )
        }

    def count(self) -> int:
        return len(self.videos)

    def items(self) -> Iterable[Tuple[Any, Image]]:
        for filename, video in self.videos.items():
            yield filename, ImageUtils.from_blob(video["thumbnail_blob"])

    def length(self, filename) -> float:
        video = self.videos[filename]
        return video["duration"] / video["duration_time_base"]

    def video_id(self, filename) -> int:
        return self.videos[filename]["video_id"]


class DbSimilarVideos:
    __slots__ = ("positions",)

    def __init__(self):
        # self.positions = deque()
        self.positions = None

    def find(self, db) -> None:
        return self.find_similar_videos(db)

    @Profiler.profile()
    def find_similar_videos(self, db: AbstractDatabase):
        miniatures: List[Miniature] = db.ensure_miniatures()
        video_indices = [m.video_id for m in miniatures]
        previous_sim = [
            row["similarity_id"]
            for row in db.get_videos(
                include=["similarity_id"], where={"video_id": video_indices}
            )
        ]
        db.set_similarities(video_indices, (None for _ in video_indices))
        try:
            self._find_similar_videos(db, miniatures)
        except Exception:
            # Restore previous similarities.
            db.set_similarities(video_indices, previous_sim)
            raise

    @classmethod
    def _find_similar_videos(
        cls, db: AbstractDatabase, miniatures: List[Miniature] = None
    ):
        imp = DbImageProvider(db)
        ac = ApproximateComparatorAnnoy(imp)
        combined = ac.get_comparable_images_cos()
        similarities = compare_miniatures_native(miniatures, combined)

        video_indices = [m.video_id for m in miniatures]
        db.set_similarities(video_indices, (-1 for _ in video_indices))

        similarities.sort(key=lambda group: (-len(group), sorted(group)[0]))
        v_indices = []
        v_sim_ids = []
        for similarity_id, group in enumerate(similarities):
            for filename in group:
                v_indices.append(imp.video_id(filename))
                v_sim_ids.append(similarity_id)
        db.set_similarities(v_indices, v_sim_ids)
