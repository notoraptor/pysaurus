import itertools
from typing import List, Any

import matplotlib.pyplot as plt

from pysaurus.core.functions import compute_nb_couples
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
    __slots__ = "keys", "groups"
    keys: List
    groups: List

    def __init__(self, keys: List[Any], groups: List[List[str]]):
        self.keys = keys
        self.groups = groups

    def __len__(self):
        return len(self.keys)


class MiniaturesPerNbGroups(MiniaturesPerKey):
    __slots__ = ()


class MiniaturesPerGray(MiniaturesPerKey):
    __slots__ = ()

    def __init__(self, keys, groups):
        super().__init__([float(key) for key in keys], groups)

class Comparisons:
    __slots__ = "miniatures_per_key", "dst_limit"

    def __init__(self, miniatures_per_key: MiniaturesPerKey, dst_limit: Fraction):
        self.miniatures_per_key = miniatures_per_key
        self.dst_limit = dst_limit

    def cross_comparisons(self):
        s = float(Fraction(255) * self.dst_limit)
        n = len(self.miniatures_per_key.keys)
        k = self.miniatures_per_key.keys
        for i in range(n):
            for j in range(i + 1, n):
                if abs(k[i] - k[j]) > s:
                    break
                yield i, j
            if (i + 1) % 1000 == 0:
                print(i + 1, "/", n)

    def count_inner_comparisons(self):
        return sum(compute_nb_couples(len(ic)) for ic in self.miniatures_per_key.groups)

    @Profiler.profile()
    def count_cross_comparisons(self):
        gs = self.miniatures_per_key.groups
        return sum(len(gs[i]) * len(gs[j]) for i, j in self.cross_comparisons())

    def inner_couples(self):
        for ic in self.miniatures_per_key.groups:
            yield from itertools.combinations(ic, 2)

    def cross_couples(self):
        for r, c in self.cross_comparisons():
            yield from itertools.product(
                self.miniatures_per_key.groups[r], self.miniatures_per_key.groups[c]
            )

    def cross_groups(self):
        gs = self.miniatures_per_key.groups
        for r, c in self.cross_comparisons():
            yield gs[r], gs[c]


@Profiler.profile()
def count_miniatures_groups(miniatures: List[Miniature]):
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
def get_miniature_grays(miniatures: List[Miniature]):
    gray_to_miniatures = {}
    for m in miniatures:
        gray_to_miniatures.setdefault(miniature_utils.global_intensity(m), []).append(
            m.identifier
        )
    g_ms = sorted(gray_to_miniatures.items(), key=lambda item: item[0])
    print("Number of colors", len(g_ms))
    print("Colors", float(min(c for c, _ in g_ms)), float(max(c for c, _ in g_ms)))
    print("Counts", min(len(g) for _, g in g_ms), max(len(g) for _, g in g_ms))
    return MiniaturesPerGray([c for c, _ in g_ms], [g for _, g in g_ms])


@Profiler.profile()
def count_nb_inner_connected(comparisons: Comparisons, rs: RawSimilarities):
    return sum(rs.couple_is_connected(*couple) for couple in comparisons.inner_couples())


@Profiler.profile()
def count_nb_cross_connected(comparisons: Comparisons, rs: RawSimilarities):
    nb_comparisons = 0
    nb_connected = 0
    for couple in comparisons.cross_couples():
        nb_comparisons += 1
        nb_connected += rs.couple_is_connected(*couple)
    return nb_comparisons, nb_connected


@Profiler.profile()
def main():
    rs = RawSimilarities.new()
    tester = DbTester()
    # gc_to_ids = count_miniatures_groups(tester.miniatures)
    gr_to_ids = get_miniature_grays(tester.miniatures)
    comparisons = Comparisons(gr_to_ids, FRAC_DST_LIMIT)

    nb_comparisons = comparisons.count_inner_comparisons()
    nb_connected = count_nb_inner_connected(comparisons, rs)
    cross_nb_comparisons, cross_nb_connected = count_nb_cross_connected(comparisons, rs)
    nb_comparisons += cross_nb_comparisons
    nb_connected += cross_nb_connected
    # nb_comparisons += comparisons.count_cross_comparisons()

    nb_max_comparisons = compute_nb_couples(len(tester.miniatures))
    print("Nb. videos", len(tester.miniatures))
    print("Nb. expected comparisons", nb_comparisons)
    print("Nb. max comparisons", nb_max_comparisons)
    print("ratio", nb_comparisons * 100 / nb_max_comparisons, "%")
    print("Nb connected", nb_connected)
    print("Expected connected", rs.count_couples())


if __name__ == "__main__":
    main()
