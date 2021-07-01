import itertools
from typing import List, Any, Tuple

import matplotlib.pyplot as plt

from pysaurus.core.functions import compute_nb_couples, get_end_index
from pysaurus.core.miniature import Miniature
from pysaurus.core.profiling import Profiler
from pysaurus.other.tests.image_management.compare_images_cpp import FRAC_DST_LIMIT
from pysaurus.other.tests.image_management.elements import miniature_utils
from pysaurus.other.tests.image_management.elements.db_tester import DbTester
from pysaurus.other.tests.image_management.elements.group_computer import (
    GroupComputer,
)
from pysaurus.other.tests.image_management.elements.raw_similarities import (
    RawSimilarities,
)
from pysaurus.core.fraction import Fraction


def draw_intensity(colors: List[float], counts: List[float]):
    plt.plot(colors, counts)
    plt.xlabel("Colors")
    plt.ylabel("# videos")
    plt.title("Number of videos per video gray average")
    plt.show()


class MiniaturesPerKey:
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


class MiniaturesPerNbGroups(MiniaturesPerKey):
    __slots__ = ()


class MiniaturesPerGray(MiniaturesPerKey):
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
def count_miniatures_groups(miniatures: List[Miniature]) -> MiniaturesPerNbGroups:
    group_computer = GroupComputer.from_pixel_distance_radius(
        pixel_distance_radius=6, group_min_size=0, print_step=2000
    )
    nb_groups_to_mins = {}
    for dm in group_computer.batch_compute_groups(miniatures):
        nb_groups_to_mins.setdefault(len(dm.pixel_groups), []).append(
            dm.miniature_identifier
        )
    g_ms = sorted(nb_groups_to_mins.items(), key=lambda item: item[0])
    print("Number of group counts", len(g_ms))
    print("Nb groups", min(c for c, _ in g_ms), max(c for c, _ in g_ms))
    print("Nb videos", min(len(g) for _, g in g_ms), max(len(g) for _, g in g_ms))
    return MiniaturesPerNbGroups([c for c, _ in g_ms], [g for _, g in g_ms])


@Profiler.profile()
def get_miniature_grays(miniatures: List[Miniature]) -> MiniaturesPerGray:
    gray_to_miniatures = {}
    for m in miniatures:
        gray_to_miniatures.setdefault(miniature_utils.global_intensity(m), []).append(
            m.identifier
        )
    g_ms = sorted(gray_to_miniatures.items(), key=lambda item: item[0])
    print("Number of colors", len(g_ms))
    print("Colors", float(min(c for c, _ in g_ms)), float(max(c for c, _ in g_ms)))
    print("Counts", min(len(g) for _, g in g_ms), max(len(g) for _, g in g_ms))
    return MiniaturesPerGray([float(c) for c, _ in g_ms], [g for _, g in g_ms])


@Profiler.profile()
def count_nb_inner_connected(comparisons: MiniaturesPerGray, rs: RawSimilarities):
    return sum(
        rs.couple_is_connected(*couple) for couple in comparisons.inner_couples()
    )


@Profiler.profile()
def count_nb_cross_connected(comparisons: MiniaturesPerGray, rs: RawSimilarities):
    nb_comparisons = 0
    nb_connected = 0
    for couple in comparisons.cross_couples():
        nb_comparisons += 1
        nb_connected += rs.couple_is_connected(*couple)
    return nb_comparisons, nb_connected


def separate_by_nb_groups(
    paths: List[str], gc_to_ids: MiniaturesPerNbGroups
) -> List[Tuple[int, List[str]]]:
    gc_to_paths = {}
    for path in paths:
        gc_to_paths.setdefault(gc_to_ids.value_to_key[path], []).append(path)
    gc_ps = sorted(gc_to_paths.items(), key=lambda item: item[0])
    return gc_ps


@Profiler.profile()
def main():
    rs = RawSimilarities.new()
    tester = DbTester()
    nb_max_comparisons = compute_nb_couples(len(tester.miniatures))

    gc_to_ids = count_miniatures_groups(
        tester.miniatures
    )  # type: MiniaturesPerNbGroups
    gr_to_ids = get_miniature_grays(tester.miniatures)  # type: MiniaturesPerGray
    ligr_l_gc_ids = [
        separate_by_nb_groups(group, gc_to_ids) for group in gr_to_ids.groups
    ]  # type: List[List[Tuple[int, List[str]]]]
    nb_cmp = sum(
        compute_nb_couples(len(ids))
        for l_gc_ids in ligr_l_gc_ids
        for _, ids in l_gc_ids
    )
    nb_cn = sum(
        rs.are_connected(a, b)
        for l_gc_ids in ligr_l_gc_ids
        for _, ids in l_gc_ids
        for a, b in itertools.combinations(ids, 2)
    )
    for r, c in gr_to_ids.cross_comparisons():
        lr = ligr_l_gc_ids[r]
        lc = ligr_l_gc_ids[c]
        for i in range(len(lr)):
            gc_i, ids_i = lr[i]
            for j in range(len(lc)):
                if abs(gc_i - lc[j][0]) > 40:
                    break
                nb_cmp += len(ids_i) * len(lc[j][1])
                nb_cn += sum(
                    rs.are_connected(a, b)
                    for a, b in itertools.product(ids_i, lc[j][1])
                )
    print("Nb. videos", len(tester.miniatures))
    print("Nb. expected comparisons", nb_cmp)
    print("Nb. max comparisons", nb_max_comparisons)
    print("ratio", nb_cmp * 100 / nb_max_comparisons, "%")
    print("Nb connected", nb_cn)
    print("Expected connected", rs.count_couples())


if __name__ == "__main__":
    main()
