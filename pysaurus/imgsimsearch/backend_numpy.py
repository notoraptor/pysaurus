from collections import namedtuple

import numpy as np

from pysaurus.core.abstract_notifier import AbstractNotifier
from pysaurus.core.miniature import Miniature, NumpyMiniature
from pysaurus.core.parallelization import USABLE_CPU_COUNT, parallelize
from pysaurus.core.profiling import Profiler
from saurus.language import say

SIMPLE_MAX_PIXEL_DISTANCE = 255 * 3
V = SIMPLE_MAX_PIXEL_DISTANCE
B = V / 2.0
V_PLUS_B = V + B


def classify_similarities_directed(
    miniatures_, edges, limit, notifier: AbstractNotifier
):
    miniatures = [m.to_numpy() for m in miniatures_]
    nb_sequences = len(miniatures)
    width = miniatures[0].width
    height = miniatures[0].height
    maximum_distance_score = SIMPLE_MAX_PIXEL_DISTANCE * width * height
    notifier.task(
        _compare_miniatures_from_numpy, nb_sequences, "videos (Python comparison)"
    )
    with Profiler(say("Numpy images comparison"), notifier=notifier):
        raw_output = list(
            parallelize(
                _compare_miniatures_from_numpy,
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
    miniatures: list[Miniature],
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
        notifier.progress(_compare_miniatures_from_numpy, i + 1, nb_sequences)


def _compare_miniatures_from_numpy(job):
    mi, mj, i, j, limit, mds = job
    return (i, j) if compare_faster(mi, mj, mds) >= limit else None


# preallocate empty array and assign slice by chrisaycock
# https://stackoverflow.com/a/42642326 (2023/09/05)


def shift_top_left(arr, fill_value=np.inf):
    result = np.empty_like(arr)
    result[0] = fill_value
    result[:, 0] = fill_value
    result[1:, 1:] = arr[:-1, :-1]
    return result


def shift_top(arr, fill_value=np.inf):
    result = np.empty_like(arr)
    result[0] = fill_value
    result[1:, :] = arr[:-1, :]
    return result


def shift_top_right(arr, fill_value=np.inf):
    result = np.empty_like(arr)
    result[0] = fill_value
    result[:, -1] = fill_value
    result[1:, :-1] = arr[:-1, 1:]
    return result


def shift_left(arr, fill_value=np.inf):
    result = np.empty_like(arr)
    result[:, 0] = fill_value
    result[:, 1:] = arr[:, :-1]
    return result


def shift_center(arr, fill_value=np.inf):
    return arr


def shift_right(arr, fill_value=np.inf):
    result = np.empty_like(arr)
    result[:, -1] = fill_value
    result[:, :-1] = arr[:, 1:]
    return result


#
def shift_bottom_left(arr, fill_value=np.inf):
    result = np.empty_like(arr)
    result[-1] = fill_value
    result[:, 0] = fill_value
    result[:-1, 1:] = arr[1:, :-1]
    return result


def shift_bottom(arr, fill_value=np.inf):
    result = np.empty_like(arr)
    result[-1] = fill_value
    result[:-1, :] = arr[1:, :]
    return result


def shift_bottom_right(arr, fill_value=np.inf):
    result = np.empty_like(arr)
    result[-1] = fill_value
    result[:, -1] = fill_value
    result[:-1, :-1] = arr[1:, 1:]
    return result


RGB = namedtuple("RGB", ("r", "g", "b"))


def np_dst(rgb1, rgb2):
    return np.nan_to_num(
        moderate(
            np.abs(rgb1.r - rgb2.r) + np.abs(rgb1.g - rgb2.g) + np.abs(rgb1.b - rgb2.b)
        ),
        nan=np.inf,
    )


def compare_faster(p1: NumpyMiniature, p2: NumpyMiniature, maximum_distance_score: int):
    # x, y to x - 1, y - 1
    top_left = RGB(shift_top_left(p2.r), shift_top_left(p2.g), shift_top_left(p2.b))
    # x, y to x, y - 1
    top = RGB(shift_top(p2.r), shift_top(p2.g), shift_top(p2.b))
    # x, y to x + 1, y - 1
    top_right = RGB(shift_top_right(p2.r), shift_top_right(p2.g), shift_top_right(p2.b))
    # x, y to x - 1, y
    left = RGB(shift_left(p2.r), shift_left(p2.g), shift_left(p2.b))
    # x, y to x, y
    center = RGB(shift_center(p2.r), shift_center(p2.g), shift_center(p2.b))
    # x, y to x + 1, y
    right = RGB(shift_right(p2.r), shift_right(p2.g), shift_right(p2.b))
    # x, y to x - 1, y + 1
    bottom_left = RGB(
        shift_bottom_left(p2.r), shift_bottom_left(p2.g), shift_bottom_left(p2.b)
    )
    # x, y to x, y + 1
    bottom = RGB(shift_bottom(p2.r), shift_bottom(p2.g), shift_bottom(p2.b))
    # x, y to x + 1, y + 1
    bottom_right = RGB(
        shift_bottom_right(p2.r), shift_bottom_right(p2.g), shift_bottom_right(p2.b)
    )

    total_distance = np.sum(
        np.minimum(
            np_dst(p1, top_left),
            np.minimum(
                np_dst(p1, top),
                np.minimum(
                    np_dst(p1, top_right),
                    np.minimum(
                        np_dst(p1, left),
                        np.minimum(
                            np_dst(p1, center),
                            np.minimum(
                                np_dst(p1, right),
                                np.minimum(
                                    np_dst(p1, bottom_left),
                                    np.minimum(
                                        np_dst(p1, bottom), np_dst(p1, bottom_right)
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
    )
    return (maximum_distance_score - total_distance) / maximum_distance_score


class SimilarityComparator:
    __slots__ = ("max_dst_score", "limit")

    def __init__(self, limit, width, height):
        self.limit = limit
        self.max_dst_score = SIMPLE_MAX_PIXEL_DISTANCE * width * height

    def are_similar(self, p1: NumpyMiniature, p2: NumpyMiniature) -> bool:
        return compare_faster(p1, p2, self.max_dst_score) >= self.limit


def moderate(x: float):
    return V_PLUS_B * x / (x + B)
