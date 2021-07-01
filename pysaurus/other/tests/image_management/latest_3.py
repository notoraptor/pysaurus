import itertools
from ctypes import Array, c_double
from typing import List, Any, Tuple, Dict, Set

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


class ListMap:
    __slots__ = "keys", "groups", "value_to_key"
    keys: List
    groups: List

    def __init__(self, keys: List[Any], groups: List[List[str]]):
        self.keys = keys
        self.groups = groups
        self.value_to_key = {
            value: key
            for key, values in zip(self.keys, self.groups)
            for value in values
        }
        assert len(self.value_to_key) == sum(len(group) for group in self.groups)

    def __len__(self):
        return len(self.keys)


class NbGroupsToPaths(ListMap):
    __slots__ = ()


class GrayToPaths(ListMap):
    __slots__ = ("j_limit",)

    def __init__(self, keys, groups, dst_limit: Fraction = FRAC_DST_LIMIT):
        super().__init__(keys, groups)
        s = float(Fraction(255) * dst_limit)
        k = self.keys
        self.j_limit = [get_end_index(k, k[i] + s, i + 1) for i in range(len(k))]

    def cross_comparisons(self):
        """Return sequence of couples of indices of groups to cross compare."""
        n = len(self.keys)
        t = self.j_limit
        for i in range(n):
            for j in range(i + 1, t[i]):
                yield i, j
            if (i + 1) % 1000 == 0:
                print(i + 1, "/", n)

    def count_inner_couples(self):
        return sum(compute_nb_couples(len(ic)) for ic in self.groups)

    @Profiler.profile()
    def count_cross_couples(self):
        gs = self.groups
        return sum(len(gs[i]) * len(gs[j]) for i, j in self.cross_comparisons())

    def inner_couples(self):
        for ic in self.groups:
            yield from itertools.combinations(ic, 2)

    def cross_couples(self):
        gs = self.groups
        for i, j in self.cross_comparisons():
            yield from itertools.product(gs[i], gs[j])

    def inner_groups(self):
        return iter(self.groups)

    def cross_groups(self):
        gs = self.groups
        for r, c in self.cross_comparisons():
            yield gs[r], gs[c]


@Profiler.profile()
def count_miniatures_groups(miniatures: List[Miniature]) -> NbGroupsToPaths:
    nb_groups_to_mins = {}
    for m in miniatures:
        nb_groups_to_mins.setdefault(m.group_signature.n, []).append(m.identifier)
    g_ms = sorted(nb_groups_to_mins.items(), key=lambda item: item[0])
    print("Number of group counts", len(g_ms))
    print("Nb groups", min(c for c, _ in g_ms), max(c for c, _ in g_ms))
    print("Nb videos", min(len(g) for _, g in g_ms), max(len(g) for _, g in g_ms))
    return NbGroupsToPaths([c for c, _ in g_ms], [g for _, g in g_ms])


@Profiler.profile()
def get_miniature_grays(miniatures: List[Miniature]) -> GrayToPaths:
    gray_to_miniatures = {}
    for m in miniatures:
        gray_to_miniatures.setdefault(miniature_utils.global_intensity(m), []).append(
            m.identifier
        )
    g_ms = sorted(gray_to_miniatures.items(), key=lambda item: item[0])
    print("Number of colors", len(g_ms))
    print("Colors", float(min(c for c, _ in g_ms)), float(max(c for c, _ in g_ms)))
    print("Counts", min(len(g) for _, g in g_ms), max(len(g) for _, g in g_ms))
    return GrayToPaths([float(c) for c, _ in g_ms], [g for _, g in g_ms])


def separate_by_nb_groups(
    paths: List[str], gc_to_ids: NbGroupsToPaths, path_to_id: Dict[str, int]
) -> List[Tuple[int, List[int]]]:
    gc_to_paths = {}
    for path in paths:
        gc_to_paths.setdefault(gc_to_ids.value_to_key[path], []).append(
            path_to_id[path]
        )
    for paths in gc_to_paths.values():
        paths.sort()
    gc_ps = sorted(gc_to_paths.items(), key=lambda item: item[0])
    return gc_ps


def find_similar_images_2(miniatures, edges):
    # type: (List[Miniature], Array[c_double]) -> List[Set[int]]
    native_alignment.classify_similarities_directed(miniatures, edges)
    graph = Graph()
    nb_miniatures = len(miniatures)
    for i in range(len(miniatures)):
        for j in range(i + 1, len(miniatures)):
            if edges[i * nb_miniatures + j] >= SIM_LIMIT:
                graph.connect(i, j)
    return [group for group in graph.pop_groups() if len(group) > 1]


@Profiler.profile()
def main():
    # rs = RawSimilarities.new()
    tester = DbTester()
    nb_miniatures = len(tester.miniatures)
    nb_max_comparisons = compute_nb_couples(len(tester.miniatures))

    gc_to_ids = count_miniatures_groups(tester.miniatures)  # type: NbGroupsToPaths
    gr_to_ids = get_miniature_grays(tester.miniatures)  # type: GrayToPaths
    path_to_id = {m.identifier: i for i, m in enumerate(tester.miniatures)}
    ligr_l_gc_ids = [
        separate_by_nb_groups(group, gc_to_ids, path_to_id)
        for group in gr_to_ids.groups
    ]  # type: List[List[Tuple[int, List[int]]]]

    from ctypes import c_double

    arr_cls = c_double * (nb_miniatures * nb_miniatures)
    cmp_map = arr_cls()
    nb_cmp = sum(
        compute_nb_couples(len(ids))
        for l_gc_ids in ligr_l_gc_ids
        for _, ids in l_gc_ids
    )
    for l_gc_ids in ligr_l_gc_ids:
        for _, ids in l_gc_ids:
            for i, j in itertools.combinations(ids, 2):
                cmp_map[i * nb_miniatures + j] = -1

    for r, c in gr_to_ids.cross_comparisons():
        lr = ligr_l_gc_ids[r]
        lc = ligr_l_gc_ids[c]
        for i in range(len(lr)):
            gc_i, ids_i = lr[i]
            for j in range(len(lc)):
                if abs(gc_i - lc[j][0]) > 40:
                    break
                nb_cmp += len(ids_i) * len(lc[j][1])
                for a, b in itertools.product(ids_i, lc[j][1]):
                    if a > b:
                        a, b = b, a
                    cmp_map[a * nb_miniatures + b] = -1

    print("Nb. videos", nb_miniatures)
    print("Nb. expected comparisons", nb_cmp)
    print("Nb. max comparisons", nb_max_comparisons)
    print("ratio", nb_cmp * 100 / nb_max_comparisons, "%")
    sim_groups = find_similar_images_2(tester.miniatures, cmp_map)
    print("Finally found", len(sim_groups), "similarity groups.")
    print(
        sum(len(g) for g in sim_groups),
        "similar images from",
        nb_miniatures,
        "total images.",
    )


if __name__ == "__main__":
    main()
