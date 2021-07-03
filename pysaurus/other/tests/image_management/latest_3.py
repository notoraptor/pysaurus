import itertools
from ctypes import Array, c_bool
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


def find_similar_images(miniatures, edges):
    # type: (List[Miniature], Array[c_bool]) -> List[Set[int]]
    native_alignment.classify_similarities_directed(miniatures, edges, SIM_LIMIT)
    graph = Graph()
    nb_miniatures = len(miniatures)
    for i in range(len(miniatures)):
        for j in range(i + 1, len(miniatures)):
            if edges[i * nb_miniatures + j]:
                graph.connect(i, j)
    return [group for group in graph.pop_groups() if len(group) > 1]


@Profiler.profile()
def main():
    tester = DbTester()
    miniatures = tester.miniatures
    nb_miniatures = len(miniatures)
    nb_max_comparisons = compute_nb_couples(len(miniatures))
    classifier = GrayClassifier.classify(miniatures)
    cmp_map = (c_bool * (nb_miniatures * nb_miniatures))()

    nb_cmp = sum(
        compute_nb_couples(len(group))
        for clf in classifier.classifiers
        for group in clf.groups
    )
    with Profiler("Collect comparisons."):
        for clf in classifier.classifiers:
            for indices in clf.groups:
                for i, j in itertools.combinations(indices, 2):
                    cmp_map[i * nb_miniatures + j] = 1

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
                        cmp_map[a * nb_miniatures + b] = 1

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
                        cmp_map[i * nb_miniatures + j] = 1

    print("Nb. videos", nb_miniatures)
    print("Nb. expected comparisons", nb_cmp)
    print("Nb. max comparisons", nb_max_comparisons)
    print("ratio", nb_cmp * 100 / nb_max_comparisons, "%")
    sim_groups = find_similar_images(miniatures, cmp_map)
    print("Finally found", len(sim_groups), "similarity groups.")
    print(
        sum(len(g) for g in sim_groups),
        "similar images from",
        nb_miniatures,
        "total images.",
    )
    for m in miniatures:
        tester.vid_dict[m.identifier].similarity_id = -1
    sim_groups.sort(
        key=lambda s: (
            len(s),
            min(tester.vid_dict[miniatures[i].identifier].length for i in s),
        )
    )
    for sim_id, indices in enumerate(sim_groups):
        for i in indices:
            tester.vid_dict[miniatures[i].identifier].similarity_id = sim_id
    tester.db.save()


if __name__ == "__main__":
    main()
