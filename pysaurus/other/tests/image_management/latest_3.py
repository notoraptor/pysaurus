import itertools
from ctypes import Array, c_double
from typing import List, Set

from pysaurus.core.fraction import Fraction
from pysaurus.core.functions import compute_nb_couples, get_end_index
from pysaurus.core.miniature_tools.graph import Graph
from pysaurus.core.miniature_tools.miniature import Miniature
from pysaurus.core.native.alignment_raptor import alignment as native_alignment
from pysaurus.core.profiling import Profiler
from pysaurus.other.tests.image_management.compare_images_cpp import (
    FRAC_DST_LIMIT,
    SIM_LIMIT,
)
from pysaurus.other.tests.image_management.elements import miniature_utils
from pysaurus.other.tests.image_management.elements.db_tester import DbTester
from pysaurus.core.native.clibrary import c_double_p, c_int_p
import numpy as np


class NbGroupsClassifier:
    __slots__ = "counts", "groups"

    def __init__(self, counts: List[int], groups: List[List[int]]):
        self.counts = counts
        self.groups = groups

    @classmethod
    def classify(cls, miniatures: List[Miniature], indices: List[int]):
        nb_to_ids = {}
        for i in indices:
            nb_to_ids.setdefault(miniatures[i].group_signature.n, []).append(i)
        nb_then_ids = sorted(nb_to_ids.items(), key=lambda item: item[0])
        return cls([count for count, _ in nb_then_ids], [ids for _, ids in nb_then_ids])


class GrayClassifier:
    __slots__ = "grays", "classifiers", "j_limit"

    def __init__(
        self,
        grays: List[float],
        classifiers: List[NbGroupsClassifier],
        dst_limit: Fraction = FRAC_DST_LIMIT,
    ):
        s = float(Fraction(255) * dst_limit)
        self.grays = grays
        self.classifiers = classifiers
        self.j_limit = [
            get_end_index(grays, grays[i] + s, i + 1) for i in range(len(grays))
        ]

    def cross_comparisons(self):
        """Return sequence of couples of indices of classifiers to cross compare."""
        n = len(self.grays)
        t = self.j_limit
        for i in range(n):
            for j in range(i + 1, t[i]):
                yield i, j
            if (i + 1) % 1000 == 0:
                print(i + 1, "/", n)
                # return

    @classmethod
    def classify(cls, miniatures: List[Miniature]):
        gray_to_identifiers = {}
        for i, m in enumerate(miniatures):
            gray_to_identifiers.setdefault(
                miniature_utils.global_intensity(m), []
            ).append(i)
        gray_to_classifier = {
            gray: NbGroupsClassifier.classify(miniatures, indices)
            for gray, indices in gray_to_identifiers.items()
        }
        gray_then_classifier = sorted(
            gray_to_classifier.items(), key=lambda item: item[0]
        )
        return cls(
            [float(gray) for gray, _ in gray_then_classifier],
            [classifier for _, classifier in gray_then_classifier],
        )


def find_similar_images(miniatures, native_edges, original_map):
    # type: (List[Miniature], Array[c_double], np.ndarray) -> List[Set[int]]
    native_alignment.classify_similarities_selected(miniatures, native_edges, SIM_LIMIT)
    graph = Graph()
    nb_miniatures = len(miniatures)
    with Profiler("Getting connections."):
        for i in range(nb_miniatures):
            for j in range(1, original_map[i, 0]):
                if original_map[i, j]:
                    graph.connect(i, original_map[i, j])
    with Profiler(f"Popping groups from {len(graph.edges)} connections."):
        return [group for group in graph.pop_groups() if len(group) > 1]


@Profiler.profile()
def main():
    # rs = RawSimilarities.new()
    tester = DbTester()
    nb_miniatures = len(tester.miniatures)
    nb_max_comparisons = compute_nb_couples(len(tester.miniatures))
    classifier = GrayClassifier.classify(tester.miniatures)

    with Profiler("Generate maps."):
        # cmp_map = (c_double * (nb_miniatures * nb_miniatures))()
        # guide_map = [[0] * nb_miniatures for _ in range(nb_miniatures)]
        original_map = np.zeros((nb_miniatures, nb_miniatures), dtype=np.int32)
        for i in range(nb_miniatures):
            original_map[i, 0] = nb_miniatures

    nb_cmp = sum(
        compute_nb_couples(len(group))
        for clf in classifier.classifiers
        for group in clf.groups
    )
    with Profiler("Collect comparisons."):
        for clf in classifier.classifiers:
            for indices in clf.groups:
                for i, j in itertools.combinations(indices, 2):
                    # cmp_map[i * nb_miniatures + j] = -1
                    original_map[i, j] = j
        for clf in classifier.classifiers:
            nb_groups = len(clf.groups)
            for i in range(nb_groups):
                count_i = clf.counts[i]
                group_i = clf.groups[i]
                for j in range(i + 1, nb_groups):
                    if abs(count_i - clf.counts[j]) > 40:
                        break
                    group_j = clf.groups[j]
                    nb_cmp += len(group_i) * len(group_j)
                    for a, b in itertools.product(group_i, group_j):
                        if a > b:
                            a, b = b, a
                        original_map[a, b] = b

        for r, c in classifier.cross_comparisons():
            clr = classifier.classifiers[r]
            clc = classifier.classifiers[c]
            for x_r in range(len(clr.counts)):
                count_r = clr.counts[x_r]
                group_r = clr.groups[x_r]
                for x_c in range(len(clc.counts)):
                    if abs(count_r - clc.counts[x_c]) > 40:
                        break
                    group_c = clc.groups[x_c]
                    nb_cmp += len(group_r) * len(group_c)
                    for i, j in itertools.product(group_r, group_c):
                        if i > j:
                            i, j = j, i
                        # cmp_map[i * nb_miniatures + j] = -1
                        original_map[i, j] = j

    with Profiler("Update maps."):
        original_map.sort()
        original_map = np.fliplr(original_map)
        original_map[:, 0] = np.sum(original_map.astype(np.bool), axis=1)
        print(original_map)
        if not original_map.flags["C_CONTIGUOUS"]:
            original_map = np.ascontiguousarray(original_map)
        native_edges = original_map.ctypes.data_as(c_int_p)

    print("Nb. videos", nb_miniatures)
    print("Nb. expected comparisons", nb_cmp)
    print("Nb. max comparisons", nb_max_comparisons)
    print("ratio", nb_cmp * 100 / nb_max_comparisons, "%")
    sim_groups = find_similar_images(tester.miniatures, native_edges, original_map)
    print("Finally found", len(sim_groups), "similarity groups.")
    print(
        sum(len(g) for g in sim_groups),
        "similar images from",
        nb_miniatures,
        "total images.",
    )


if __name__ == "__main__":
    main()
