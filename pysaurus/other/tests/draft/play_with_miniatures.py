from typing import Tuple, List, Optional

from pysaurus.core.database.database import Database
from pysaurus.core.fraction import Fraction
from pysaurus.core.functions import pgcd, flat_to_coord
from pysaurus.core.miniature_tools.miniature import Miniature
from pysaurus.core.profiling import Profiler
from pysaurus.core.testing import TEST_LIST_FILE_PATH


def simplify_fraction(a, b):
    # type: (int, int) -> Tuple[int, int]
    d = pgcd(a, b)
    return a // d, b // d


def compute_fraction(a, b):
    # type: (int, int) -> float
    return a / b


TOP_LEFT = 0
CROSS_LEFT = 1
TOP_CENTER = 2
CROSS_RIGHT = 3
TOP_RIGHT = 4
CENTER_RIGHT = 5
BOTTOM_RIGHT = 6
BOTTOM_CENTER = 7
BOTTOM_LEFT = 8
CENTER_LEFT = 9
CENTER_CENTER = 10

ZONE_TO_POS = [TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT]


class Zone:
    __slots__ = ("zone",)
    TO_STRING = [
        "top left",
        "cross left",
        "top center",
        "cross right",
        "top right",
        "center right",
        "bottom right",
        "bottom center",
        "bottom left",
        "center left",
        "center",
    ]

    def __init__(self, zone):
        self.zone = zone

    def __str__(self):
        return self.TO_STRING[self.zone]


def whitest_region(miniature):
    # type: (Miniature) -> int
    width_split = miniature.width // 2
    height_split = miniature.height // 2
    accum = [0] * 4
    count = [0] * 4
    zones = [None] * 4  # type: List[Optional[Fraction]]
    for i in range(len(miniature.r)):
        r = miniature.r[i]
        g = miniature.g[i]
        b = miniature.b[i]
        x, y = flat_to_coord(i, miniature.width)
        zone = 2 * (x >= width_split) + (y >= height_split)
        accum[zone] += r + g + b
        count[zone] += 1
    for i in range(4):
        zones[i] = Fraction(accum[i], 3 * count[i])
    intensities = {}
    for zone, intensity in enumerate(zones):
        intensities.setdefault(intensity, []).append(zone)
    if len(intensities) == len(zones):
        return ZONE_TO_POS[intensities[max(zones)][0]]
    max_nb_zones = max(len(local_zones) for local_zones in intensities.values())
    max_intensity = max(
        intensity
        for intensity in intensities
        if len(intensities[intensity]) == max_nb_zones
    )
    max_zones = intensities[max_intensity]
    if len(max_zones) == 1:
        return ZONE_TO_POS[max_zones[0]]
    if len(max_zones) == 2:
        couple = tuple(sorted(max_zones))
        if couple == (0, 1):
            return TOP_CENTER
        if couple == (0, 2):
            return CENTER_LEFT
        if couple == (0, 3):
            return CROSS_LEFT
        if couple == (1, 2):
            return CROSS_RIGHT
        if couple == (1, 3):
            return CENTER_RIGHT
        if couple == (2, 3):
            return BOTTOM_CENTER
        raise ValueError(couple)
    if len(max_zones) == 3:
        triple = tuple(sorted(max_zones))
        if triple == (0, 1, 2):
            return TOP_LEFT
        if triple == (0, 1, 3):
            return TOP_RIGHT
        if triple == (1, 2, 3):
            return BOTTOM_LEFT
        if triple == (0, 2, 3):
            return BOTTOM_RIGHT
        raise ValueError(triple)
    if len(max_zones) == 4:
        return CENTER_CENTER


class SuperMiniature:
    __slots__ = "miniature", "intensity", "zone"

    def __init__(self, miniature):
        self.miniature = miniature
        self.intensity = miniature.global_intensity()
        self.zone = whitest_region(miniature)

    @property
    def comparator(self):
        return self.intensity, self.zone

    def __hash__(self):
        return hash(self.comparator)

    def __eq__(self, other):
        return self.comparator == other.comparator

    def __lt__(self, other):
        return self.comparator < other.comparator


def main():
    database = Database.load_from_list_file_path(TEST_LIST_FILE_PATH)
    with Profiler("Getting miniatures:"):
        miniatures_dict = database.ensure_miniatures()
    print(len(miniatures_dict), "miniature(s)")
    miniatures = list(miniatures_dict.values())
    intensities = []
    for i, miniature in enumerate(miniatures):
        intensities.append(SuperMiniature(miniature))
        if (i + 1) % 1000 == 0:
            print(i + 1, "...")
    intensities.sort()
    count_inequalities = 0
    for i in range(1, len(intensities)):
        if intensities[i - 1].comparator != intensities[i].comparator:
            count_inequalities += 1
            print(
                "Different here",
                intensities[i].intensity,
                float(intensities[i].intensity),
                Zone(intensities[i].zone),
                intensities[i].miniature.identifier,
            )
            thumb_path = database.get_video_from_filename(
                intensities[i].miniature.identifier
            ).thumbnail_path
            print("file://%s" % thumb_path)
            print("xdg-open", thumb_path)
            print()
    print(count_inequalities, "/", len(intensities) - 1, "inequalities.")
    print(intensities[0].intensity, float(intensities[0].intensity))
    print(intensities[-1].intensity, float(intensities[-1].intensity))


if __name__ == "__main__":
    main()
