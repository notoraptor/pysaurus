from multiprocessing import Pool
from typing import List

from pysaurus.core import job_notifications
from pysaurus.core.constants import USABLE_CPU_COUNT
from pysaurus.core.profiling import Profiler
from pysaurus.database.miniature_tools.miniature import Miniature

SIMPLE_MAX_PIXEL_DISTANCE = 255 * 3
V = SIMPLE_MAX_PIXEL_DISTANCE
B = V / 2.0
V_PLUS_B = V + B


def moderate(x: float):
    return V_PLUS_B * x / (x + B)


def pixel_distance(p1, x, y, p2, local_x, local_y, width):
    index_p1 = x + y * width
    index_p2 = local_x + local_y * width
    return moderate(
        abs(p1.r[index_p1] - p2.r[index_p2])
        + abs(p1.g[index_p1] - p2.g[index_p2])
        + abs(p1.b[index_p1] - p2.b[index_p2])
    )


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


def _comparison_jobs(
    miniatures: List[Miniature], edges, limit: float, mds: int, job_notifier
):
    nb_sequences = len(miniatures)
    for i in range(nb_sequences):
        for j in range(i + 1, nb_sequences):
            if edges[i * nb_sequences + j]:
                edges[i * nb_sequences + j] = 0
                yield miniatures[i], miniatures[j], i, j, limit, mds
        job_notifier.progress(None, i + 1, nb_sequences)


def _job_compare(job):
    mi, mj, i, j, limit, mds = job
    ok = compare_faster(mi, mj, mi.width, mi.height, mds) >= limit
    return (i, j) if ok else None


def classify_similarities_directed(miniatures, edges, limit, database):
    nb_sequences = len(miniatures)
    width = miniatures[0].width
    height = miniatures[0].height
    maximum_distance_score = SIMPLE_MAX_PIXEL_DISTANCE * width * height
    job_notifier = job_notifications.CompareMiniaturesFromPython(
        nb_sequences, database.notifier
    )
    with Profiler(
        database.lang.profile_classify_similarities_python.format(
            cpu_count=USABLE_CPU_COUNT
        ),
        notifier=database.notifier,
    ):
        with Pool(USABLE_CPU_COUNT) as p:
            raw_output = list(
                p.imap(
                    _job_compare,
                    _comparison_jobs(
                        miniatures, edges, limit, maximum_distance_score, job_notifier
                    ),
                    chunksize=100,
                )
            )
    for couple in raw_output:
        if couple:
            i, j = couple
            edges[i * nb_sequences + j] = 1