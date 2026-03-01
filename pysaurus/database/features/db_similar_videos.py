from typing import Any, Iterable

from PIL.Image import Image

from pysaurus.core.fraction import Fraction
from pysaurus.core.graph import Graph
from pysaurus.core.miniature import Miniature
from pysaurus.core.modules import ImageUtils
from pysaurus.core.profiling import Profiler
from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.imgsimsearch.abstract_approximate_comparator import (
    AbstractApproximateComparator,
)
from pysaurus.imgsimsearch.abstract_image_provider import AbstractImageProvider
from pysaurus.imgsimsearch.approximate_comparator_numpy import (
    ApproximateComparatorNumpy,
)
from pysaurus.imgsimsearch.python_fine_comparator import compare_miniatures
from pysaurus.video.video_pattern import VideoPattern

SIM_LIMIT = float(Fraction(88, 100))


class _CompareAllProvider(AbstractImageProvider):
    """Wrapper that forces all videos to be compared (similarity always None)."""

    __slots__ = ("_imp",)

    def __init__(self, imp: AbstractImageProvider):
        self._imp = imp

    def count(self) -> int:
        return self._imp.count()

    def items(self) -> Iterable[tuple[Any, Image]]:
        return self._imp.items()

    def length(self, filename) -> float:
        return self._imp.length(filename)

    def similarity(self, filename) -> int | None:
        return None


class DbImageProvider(AbstractImageProvider):
    __slots__ = ("videos",)

    def __init__(self, db: AbstractDatabase):
        self.videos: dict[str, VideoPattern] = {
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

    def items(self) -> Iterable[tuple[str, Image]]:
        for filename, video in self.videos.items():
            yield filename, ImageUtils.from_blob(video.thumbnail)

    def length(self, filename) -> float:
        video = self.videos[filename]
        return video.duration / video.duration_time_base

    def similarity(self, filename) -> int | None:
        return self.videos[filename].similarity_id

    def video_id(self, filename) -> int:
        return self.videos[filename].video_id

    def to_sortable_group(self, group: set[str]) -> tuple:
        return (
            len(group),
            -max(self.videos[filename].date.time for filename in group),
            sorted(group)[0],
        )


class DbSimilarVideos:
    @classmethod
    @Profiler.profile()
    def find_similar_videos(cls, db: AbstractDatabase) -> None:
        miniatures: list[Miniature] = db.algos.ensure_miniatures()
        similarities, imp = cls._compute_similar_videos(
            db, miniatures, ApproximateComparatorNumpy
        )
        previous_sim = {
            video.video_id: video.similarity_id for video in imp.videos.values()
        }
        with db.to_save():
            try:
                cls._apply_similarities(db, miniatures, similarities, imp)
            except Exception:
                db.ops.set_similarities(previous_sim)
                raise

    @classmethod
    def _apply_similarities(
        cls,
        db: AbstractDatabase,
        miniatures: list[Miniature],
        similarities: list[set[str]],
        imp: DbImageProvider,
    ):
        video_indices = [m.video_id for m in miniatures]
        db.ops.set_similarities({video_id: -1 for video_id in video_indices})

        similarities.sort(key=imp.to_sortable_group)
        db.ops.set_similarities(
            {
                imp.video_id(filename): similarity_id
                for similarity_id, group in enumerate(similarities)
                for filename in group
            }
        )

    @classmethod
    def _compute_similar_videos(
        cls,
        db: AbstractDatabase,
        miniatures: list[Miniature],
        comparator_class: type[AbstractApproximateComparator],
        compare_all: bool = False,
    ) -> tuple[list[set[str]], DbImageProvider]:
        """Compute similarity groups (read-only, does not write to db).

        Args:
            db: Database to read videos from.
            miniatures: Pre-computed miniatures.
            comparator_class: Approximate comparator class to use.
            compare_all: If True, compare all videos (ignore existing
                similarity_id). If False, only compare new videos and
                merge with existing similarity groups.

        Returns:
            Tuple of (similarity groups, image provider).
        """
        with Profiler("Loading thumbnails from database.", db.notifier):
            imp = DbImageProvider(db)
        comparator_imp = _CompareAllProvider(imp) if compare_all else imp
        ac = comparator_class(comparator_imp)
        combined = ac.get_comparable_images_cos()
        new_similarities = compare_miniatures(miniatures, combined, SIM_LIMIT)

        if compare_all:
            return new_similarities, imp

        # Merge with old similarities
        old_similarities = {}
        for filename in imp.videos:
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
        return [group for group in graph.pop_groups() if len(group) > 1], imp
