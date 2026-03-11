from pysaurus.core.graph import Graph
from pysaurus.core.profiling import Profiler
from pysaurus.database.abstract_database import AbstractDatabase
from pysaurus.video.video_pattern import VideoPattern

FIELD = "similarity_id_reencoded"
MAX_DURATION_DIFF = 0.25  # seconds
MAX_TITLE_DIFF_RATIO = 0.5  # suffix/prefix length < 50% of shorter title
MIN_TITLE_DIFF = 8  # absolute minimum allowed difference in characters


class DbSimilarReencoded:
    @classmethod
    @Profiler.profile()
    def find_similar_reencoded(cls, db: AbstractDatabase) -> None:
        videos = db.get_videos(
            include=[
                "video_id",
                "filename",
                "duration",
                "duration_time_base",
                "date",
                FIELD,
            ],
            where={"readable": True},
        )
        similarities, video_map = cls._compute(db, videos)
        previous = {v.video_id: getattr(v, FIELD) for v in videos}
        with db.to_save():
            try:
                cls._apply(db, videos, similarities, video_map)
            except Exception:
                db.ops.set_similarities(previous, field=FIELD)
                raise

    @classmethod
    def _compute(
        cls, db: AbstractDatabase, videos: list[VideoPattern]
    ) -> tuple[list[set[str]], dict[str, VideoPattern]]:
        video_map = {v.filename.path: v for v in videos}
        with Profiler("Finding re-encoded videos.", db.notifier):
            durations = []
            for v in videos:
                dtb = v.duration_time_base or 1
                durations.append((v, v.duration / dtb))
            durations.sort(key=lambda x: x[1])

            graph = Graph()
            n = len(durations)
            for i in range(n):
                vi, di = durations[i]
                j = i + 1
                while j < n and durations[j][1] - di <= MAX_DURATION_DIFF:
                    vj, _ = durations[j]
                    if cls._titles_match(vi, vj):
                        graph.connect(vi.filename.path, vj.filename.path)
                    j += 1

            groups = [g for g in graph.pop_groups() if len(g) > 1]
        return groups, video_map

    @classmethod
    def _apply(
        cls,
        db: AbstractDatabase,
        videos: list[VideoPattern],
        similarities: list[set[str]],
        video_map: dict[str, VideoPattern],
    ):
        db.ops.set_similarities({v.video_id: -1 for v in videos}, field=FIELD)
        similarities.sort(key=lambda g: cls._sortable_group(g, video_map))
        db.ops.set_similarities(
            {
                video_map[filename].video_id: sim_id
                for sim_id, group in enumerate(similarities)
                for filename in group
            },
            field=FIELD,
        )

    @staticmethod
    def _sortable_group(group: set[str], video_map: dict[str, VideoPattern]) -> tuple:
        return (
            len(group),
            -max(video_map[f].date.time for f in group),
            sorted(group)[0],
        )

    @staticmethod
    def _titles_match(v1: VideoPattern, v2: VideoPattern) -> bool:
        title1 = v1.filename.file_title
        title2 = v2.filename.file_title
        if len(title1) <= len(title2):
            shorter, longer = title1, title2
        else:
            shorter, longer = title2, title1
        if not shorter:
            return False
        if shorter not in longer:
            return False
        diff_len = len(longer) - len(shorter)
        return diff_len < max(len(shorter) * MAX_TITLE_DIFF_RATIO, MIN_TITLE_DIFF)
