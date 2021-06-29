from pysaurus.core.functions import compute_nb_couples
from pysaurus.other.tests.image_management.latest import load_default_database
from pysaurus.core.profiling import Profiler
from typing import List
from pysaurus.other.tests.image_management.elements.corner_group_computer import (
    CornerGroupComputer,
)
from pysaurus.other.tests.image_management.elements.spaced_points import (
    SpacedPoints,
    SpacedPoints32To64,
)
from pysaurus.other.tests.image_management.elements import miniature_utils
import matplotlib.pyplot as plt
from pysaurus.other.tests.image_management.compare_images_cpp import SIM_LIMIT
from pysaurus.other.tests.image_management.elements.raw_similarities import RawSimilarities


def draw_intensity(colors: List[float], counts: List[float]):
    plt.plot(colors, counts)
    plt.xlabel("Colors")
    plt.ylabel("# videos")
    plt.title("Number of videos per video gray average")
    plt.show()


def main():
    group_computer = CornerGroupComputer.from_pixel_distance_radius(
        pixel_distance_radius=6, group_min_size=0, print_step=2000
    )
    spaced_color = SpacedPoints(256, 6)
    spaced_position = SpacedPoints32To64(2)
    rs = RawSimilarities.new()

    db = load_default_database()
    videos = db.get_videos("readable", "with_thumbnails")
    min_dict = {m.identifier: m for m in db.ensure_miniatures(return_miniatures=True)}
    vid_dict = {v.filename.path: v for v in videos}
    miniatures = [min_dict[v.filename.path] for v in videos]
    # dec_mins = group_computer.batch_compute_groups(miniatures)
    gray_to_miniatures = {}
    for m in miniatures:
        gray_to_miniatures.setdefault(miniature_utils.global_intensity(m), []).append(m)
    gray_and_miniatures = sorted(gray_to_miniatures.items(), key=lambda item: item[0])
    colors = []
    counts = []
    for color, mins in gray_and_miniatures:
        colors.append(float(color))
        counts.append(len(mins))
    assert sum(counts) == len(miniatures)
    print("Number of colors", len(colors))
    print("Colors", min(colors), max(colors))
    print("Counts", min(counts), max(counts))
    with Profiler("Collect expected comparisons"):
        nb_comparisons = sum(compute_nb_couples(n) for n in counts)
        nb_connected = 0
        for i in range(len(gray_and_miniatures)):
            gray_i, mins_i = gray_and_miniatures[i]
            gray_i = float(gray_i)
            for x in range(len(mins_i)):
                for y in range(x + 1, len(mins_i)):
                    nb_connected += rs.are_connected(mins_i[x].identifier, mins_i[y].identifier)
            for j in range(i + 1, len(gray_and_miniatures)):
                gray_j, mins_j = gray_and_miniatures[j]
                if (255 - abs(gray_i - float(gray_j))) / 255 < SIM_LIMIT:
                    break
                nb_comparisons += len(mins_i) * len(mins_j)
                for m_i in mins_i:
                    for m_j in mins_j:
                        nb_connected += rs.are_connected(m_i.identifier, m_j.identifier)
            if (i + 1) % 500 == 0:
                print(i + 1, "/", len(gray_and_miniatures))
    # with Profiler("Compute nb. expected comparisons"):
    #     nb_comparisons = sum(compute_nb_couples(n) for n in counts)
    #     for i in range(len(colors)):
    #         for j in range(i + 1, len(colors)):
    #             if (255 - abs(colors[i] - colors[j])) / 255 < SIM_LIMIT:
    #                 break
    #             nb_comparisons += counts[i] * counts[j]
    #         if (i + 1) % 1000 == 0:
    #             print(i + 1, "/", len(colors))
    nb_max_comparisons = compute_nb_couples(len(miniatures))
    print("Nb. videos", len(miniatures))
    print("Nb. expected comparisons", nb_comparisons)
    print("Nb. max comparisons", nb_max_comparisons)
    print("ratio", nb_comparisons * 100 / nb_max_comparisons, "%")
    print("Nb connected", nb_connected)
    print("Expected connected", rs.count_couples())



if __name__ == '__main__':
    main()
