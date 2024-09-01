from typing import List

from pysaurus.core.abstract_notifier import AbstractNotifier
from pysaurus.core.parallelization import USABLE_CPU_COUNT, parallelize
from pysaurus.core.profiling import Profiler
from pysaurus.miniature.miniature import Miniature
from saurus.language import say

SIMPLE_MAX_PIXEL_DISTANCE = 255 * 3
V = SIMPLE_MAX_PIXEL_DISTANCE
B = V / 2.0
V_PLUS_B = V + B


def classify_similarities_directed(
    miniatures, edges, limit, notifier: AbstractNotifier
):
    nb_sequences = len(miniatures)
    width = miniatures[0].width
    height = miniatures[0].height
    maximum_distance_score = SIMPLE_MAX_PIXEL_DISTANCE * width * height
    notifier.task(
        _compare_miniatures_from_python, nb_sequences, "videos (Python comparison)"
    )
    with Profiler(say("Python images comparison"), notifier=notifier):
        raw_output = list(
            parallelize(
                _compare_miniatures_from_python,
                _comparison_jobs(
                    miniatures, edges, limit, maximum_distance_score, notifier
                ),
                cpu_count=USABLE_CPU_COUNT,
                chunksize=100,
            )
        )
    for couple in raw_output:
        if couple:
            i, j = couple
            edges[i * nb_sequences + j] = 1


def _comparison_jobs(
    miniatures: List[Miniature],
    edges,
    limit: float,
    mds: int,
    notifier: AbstractNotifier,
):
    nb_sequences = len(miniatures)
    for i in range(nb_sequences):
        for j in range(i + 1, nb_sequences):
            if edges[i * nb_sequences + j]:
                edges[i * nb_sequences + j] = 0
                yield miniatures[i], miniatures[j], i, j, limit, mds
        notifier.progress(_compare_miniatures_from_python, i + 1, nb_sequences)


def _compare_miniatures_from_python(job):
    mi, mj, i, j, limit, mds = job
    ok = compare_faster(mi, mj, mi.width, mi.height, mds) >= limit
    return (i, j) if ok else None


def compare_faster(
    p1: Miniature, p2: Miniature, width: int, height: int, maximum_distance_score: int
):
    # x, y:
    # 0, 0
    total_distance = min(
        pixel_distance(p1, 0, 0, p2, 0, 0, width),
        pixel_distance(p1, 0, 0, p2, 1, 0, width),
        pixel_distance(p1, 0, 0, p2, 0, 1, width),
        pixel_distance(p1, 0, 0, p2, 1, 1, width),
    )
    # width - 1, 0
    total_distance += min(
        pixel_distance(p1, width - 1, 0, p2, width - 2, 0, width),
        pixel_distance(p1, width - 1, 0, p2, width - 1, 0, width),
        pixel_distance(p1, width - 1, 0, p2, width - 2, 1, width),
        pixel_distance(p1, width - 1, 0, p2, width - 1, 1, width),
    )
    # 0, height - 1
    total_distance += min(
        pixel_distance(p1, 0, height - 1, p2, 0, height - 1, width),
        pixel_distance(p1, 0, height - 1, p2, 1, height - 1, width),
        pixel_distance(p1, 0, height - 1, p2, 0, height - 2, width),
        pixel_distance(p1, 0, height - 1, p2, 1, height - 2, width),
    )
    # width - 1, height - 1
    total_distance += min(
        pixel_distance(p1, width - 1, height - 1, p2, width - 2, height - 1, width),
        pixel_distance(p1, width - 1, height - 1, p2, width - 1, height - 1, width),
        pixel_distance(p1, width - 1, height - 1, p2, width - 2, height - 2, width),
        pixel_distance(p1, width - 1, height - 1, p2, width - 1, height - 2, width),
    )
    # x, 0
    for x in range(1, width - 1):
        total_distance += min(
            pixel_distance(p1, x, 0, p2, x - 1, 0, width),
            pixel_distance(p1, x, 0, p2, x, 0, width),
            pixel_distance(p1, x, 0, p2, x + 1, 0, width),
            pixel_distance(p1, x, 0, p2, x - 1, 1, width),
            pixel_distance(p1, x, 0, p2, x, 1, width),
            pixel_distance(p1, x, 0, p2, x + 1, 1, width),
        )
    # x, height - 1
    for x in range(1, width - 1):
        total_distance += min(
            pixel_distance(p1, x, height - 1, p2, x - 1, height - 1, width),
            pixel_distance(p1, x, height - 1, p2, x, height - 1, width),
            pixel_distance(p1, x, height - 1, p2, x + 1, height - 1, width),
            pixel_distance(p1, x, height - 1, p2, x - 1, height - 2, width),
            pixel_distance(p1, x, height - 1, p2, x, height - 2, width),
            pixel_distance(p1, x, height - 1, p2, x + 1, height - 2, width),
        )
    for y in range(1, height - 1):
        # 0, y
        total_distance += min(
            pixel_distance(p1, 0, y, p2, 0, y - 1, width),
            pixel_distance(p1, 0, y, p2, 1, y - 1, width),
            pixel_distance(p1, 0, y, p2, 0, y, width),
            pixel_distance(p1, 0, y, p2, 1, y, width),
            pixel_distance(p1, 0, y, p2, 0, y + 1, width),
            pixel_distance(p1, 0, y, p2, 1, y + 1, width),
        )
        # width - 1, y
        total_distance += min(
            pixel_distance(p1, width - 1, y, p2, width - 2, y - 1, width),
            pixel_distance(p1, width - 1, y, p2, width - 1, y - 1, width),
            pixel_distance(p1, width - 1, y, p2, width - 2, y, width),
            pixel_distance(p1, width - 1, y, p2, width - 1, y, width),
            pixel_distance(p1, width - 1, y, p2, width - 2, y + 1, width),
            pixel_distance(p1, width - 1, y, p2, width - 1, y + 1, width),
        )
    # x in [1; width - 2], y in [1; height - 2]
    remaining_size = (width - 2) * (height - 2)
    for index in range(0, remaining_size):
        x = index % (width - 2) + 1
        y = index // (width - 2) + 1
        total_distance += min(
            pixel_distance(p1, x, y, p2, x - 1, y - 1, width),
            pixel_distance(p1, x, y, p2, x, y - 1, width),
            pixel_distance(p1, x, y, p2, x + 1, y - 1, width),
            pixel_distance(p1, x, y, p2, x - 1, y, width),
            pixel_distance(p1, x, y, p2, x, y, width),
            pixel_distance(p1, x, y, p2, x + 1, y, width),
            pixel_distance(p1, x, y, p2, x - 1, y + 1, width),
            pixel_distance(p1, x, y, p2, x, y + 1, width),
            pixel_distance(p1, x, y, p2, x + 1, y + 1, width),
        )
    return (maximum_distance_score - total_distance) / maximum_distance_score


def pixel_distance(p1, x, y, p2, local_x, local_y, width):
    index_p1 = x + y * width
    index_p2 = local_x + local_y * width
    return moderate(
        abs(p1.r[index_p1] - p2.r[index_p2])
        + abs(p1.g[index_p1] - p2.g[index_p2])
        + abs(p1.b[index_p1] - p2.b[index_p2])
    )


def moderate(x: float):
    return V_PLUS_B * x / (x + B)


class SimilarityComparator:
    __slots__ = ("max_dst_score", "limit", "width", "height")

    def __init__(self, limit, width, height):
        self.width = width
        self.height = height
        self.limit = limit
        self.max_dst_score = SIMPLE_MAX_PIXEL_DISTANCE * width * height

    def are_similar(self, p1: Miniature, p2: Miniature) -> bool:
        return (
            compare_faster(p1, p2, self.width, self.height, self.max_dst_score)
            >= self.limit
        )
