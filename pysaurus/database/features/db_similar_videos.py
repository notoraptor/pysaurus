from typing import Any, Iterable, List, Set, Tuple

from PIL.Image import Image

from pysaurus.core.fraction import Fraction
from pysaurus.core.graph import Graph
from pysaurus.core.miniature import Miniature
from pysaurus.core.modules import ImageUtils
from pysaurus.core.profiling import Profiler
from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.imgsimsearch.abstract_image_provider import AbstractImageProvider
from pysaurus.imgsimsearch.approximate_comparator_annoy import (
    ApproximateComparatorAnnoy,
)
from pysaurus.imgsimsearch.python_fine_comparator import compare_miniatures

SIM_LIMIT = float(Fraction(88, 100))


class DbImageProvider(AbstractImageProvider):
    __slots__ = ("videos",)

    def __init__(self, db: AbstractDatabase):
        self.videos = {
            video.filename.path: video
            for video in db.get_videos(
                include=[
                    "video_id",
                    "filename",
                    "thumbnail",
                    "duration",
                    "duration_time_base",
                    "date",
                    "similarity_id",
                ],
                where={"readable": True, "with_thumbnails": True},
            )
        }

    def count(self) -> int:
        return len(self.videos)

    def items(self) -> Iterable[Tuple[Any, Image]]:
        for filename, video in self.videos.items():
            yield filename, ImageUtils.from_blob(video.thumbnail)

    def length(self, filename) -> float:
        video = self.videos[filename]
        return video.duration / video.duration_time_base

    def video_id(self, filename) -> int:
        return self.videos[filename].video_id

    def similarity(self, filename) -> int | None:
        return self.videos[filename].similarity_id

    def to_sortable_group(self, group: Set[str]) -> Tuple:
        return (
            len(group),
            -max(self.videos[filename].date.time for filename in group),
            sorted(group)[0],
        )


class DbSimilarVideos:
    @classmethod
    @Profiler.profile()
    def find_similar_videos(cls, db: AbstractDatabase) -> None:
        miniatures: List[Miniature] = db.ensure_miniatures()
        video_indices = [m.video_id for m in miniatures]
        previous_sim = [
            row.similarity_id
            for row in db.get_videos(
                include=["similarity_id"], where={"video_id": video_indices}
            )
        ]
        with db.to_save():
            # db.set_similarities({video_id: None for video_id in video_indices})
            try:
                cls._find_similar_videos(db, miniatures)
            except Exception:
                # Restore previous similarities.
                db.set_similarities(
                    {
                        video_id: prev_sim_id
                        for video_id, prev_sim_id in zip(video_indices, previous_sim)
                    }
                )
                raise

    @classmethod
    def _find_similar_videos(
        cls, db: AbstractDatabase, miniatures: List[Miniature] = None
    ):
        imp = DbImageProvider(db)
        ac = ApproximateComparatorAnnoy(imp)
        combined = ac.get_comparable_images_cos()
        new_similarities = compare_miniatures(miniatures, combined, SIM_LIMIT)

        old_similarities = {}
        for filename, _ in imp.items():
            similarity_id = imp.similarity(filename)
            if similarity_id not in (None, -1):
                old_similarities.setdefault(similarity_id, []).append(filename)
        graph = Graph()
        for old_similarity_group in old_similarities.values():
            if len(old_similarity_group) > 1:
                f, *fs = old_similarity_group
                for other in fs:
                    graph.connect(f, other)
        for group in new_similarities:
            f, *fs = group
            for other in fs:
                graph.connect(f, other)
        similarities = [group for group in graph.pop_groups() if len(group) > 1]

        video_indices = [m.video_id for m in miniatures]
        db.set_similarities({video_id: -1 for video_id in video_indices})

        similarities.sort(key=imp.to_sortable_group)
        db.set_similarities(
            {
                imp.video_id(filename): similarity_id
                for similarity_id, group in enumerate(similarities)
                for filename in group
            }
        )
