import itertools

from pysaurus.core.functions import compute_nb_couples
from pysaurus.other.tests.image_management.latest import load_default_database
from pysaurus.core.profiling import Profiler
from typing import List, Tuple, Any
from pysaurus.other.tests.image_management.elements.group_computer import (
    GroupComputer,
)
from pysaurus.other.tests.image_management.elements.spaced_points import (
    SpacedPoints,
    SpacedPoints32To64,
)
from pysaurus.other.tests.image_management.elements import miniature_utils
import matplotlib.pyplot as plt
from pysaurus.other.tests.image_management.compare_images_cpp import SIM_LIMIT
from pysaurus.other.tests.image_management.elements.raw_similarities import RawSimilarities
from pysaurus.other.tests.image_management.elements.db_tester import DbTester
from pysaurus.core.miniature import Miniature


def min_and_max(values):
    iterable_values = iter(values)
    min_value = max_value = next(iterable_values)
    for value in iterable_values:
        min_value = min(min_value, value)
        max_value = max(max_value, value)
    return min_value, max_value


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


class Comparisons:
    __slots__ = "miniatures_per_key", "sim_limit"

    def __init__(self, miniatures_per_key: MiniaturesPerKey, sim_limit):
        self.miniatures_per_key = miniatures_per_key
        self.sim_limit = sim_limit

    def cross_comparisons(self):
        n = len(self.miniatures_per_key.keys)
        for i in range(n):
            gray_i = float(self.miniatures_per_key.keys[i])
            for j in range(i + 1, n):
                if (255 - abs(gray_i - float(self.miniatures_per_key.keys[j]))) / 255 < self.sim_limit:
                    break
                yield i, j
            if (i + 1) % 1000 == 0:
                print(i + 1, "/", n)

    def count_inner_comparisons(self):
        return sum(compute_nb_couples(len(ic)) for ic in self.miniatures_per_key.groups)

    def inner_couples(self):
        for ic in self.miniatures_per_key.groups:
            yield from itertools.combinations(ic, 2)

    def cross_couples(self):
        for r, c in self.cross_comparisons():
            yield from itertools.product(self.miniatures_per_key.groups[r], self.miniatures_per_key.groups[c])


@Profiler.profile()
def count_miniatures_groups(miniatures: List[Miniature]):
    group_computer = GroupComputer.from_pixel_distance_radius(
        pixel_distance_radius=6, group_min_size=0, print_step=2000
    )
    nb_groups_to_mins = {}
    for dm in group_computer.batch_compute_groups(miniatures):
        nb_groups_to_mins.setdefault(len(dm.pixel_groups), []).append(dm.miniature_identifier)
    g_ms = sorted(nb_groups_to_mins.items(), key=lambda item: item[0])
    print("Number of group counts", len(g_ms))
    print("Nb groups", min(c for c, _ in g_ms), max(c for c, _ in g_ms))
    print("Nb videos", min(len(g) for _, g in g_ms), max(len(g) for _, g in g_ms))
    return MiniaturesPerNbGroups([c for c, _ in g_ms], [g for _, g in g_ms])


@Profiler.profile()
def get_miniature_grays(miniatures: List[Miniature]):
    gray_to_miniatures = {}
    for m in miniatures:
        gray_to_miniatures.setdefault(miniature_utils.global_intensity(m), []).append(m.identifier)
    g_ms = sorted(gray_to_miniatures.items(), key=lambda item: item[0])
    print("Number of colors", len(g_ms))
    print("Colors", float(min(c for c, _ in g_ms)), float(max(c for c, _ in g_ms)))
    print("Counts", min(len(g) for _, g in g_ms), max(len(g) for _, g in g_ms))
    return MiniaturesPerGray([c for c, _ in g_ms], [g for _, g in g_ms])


@Profiler.profile()
def main():
    rs = RawSimilarities.new()
    tester = DbTester()
    # gc_to_ids = count_miniatures_groups(tester.miniatures)
    gr_to_ids = get_miniature_grays(tester.miniatures)
    comparisons = Comparisons(gr_to_ids, SIM_LIMIT)
    nb_comparisons = comparisons.count_inner_comparisons()
    nb_connected = 0
    with Profiler("Count and check comparisons"):
        for couple in comparisons.inner_couples():
            nb_connected += rs.are_connected(*couple)
        for couple in comparisons.cross_couples():
            nb_comparisons += 1
            nb_connected += rs.are_connected(*couple)
    nb_max_comparisons = compute_nb_couples(len(tester.miniatures))
    print("Nb. videos", len(tester.miniatures))
    print("Nb. expected comparisons", nb_comparisons)
    print("Nb. max comparisons", nb_max_comparisons)
    print("ratio", nb_comparisons * 100 / nb_max_comparisons, "%")
    print("Nb connected", nb_connected)
    print("Expected connected", rs.count_couples())


if __name__ == '__main__':
    main()
