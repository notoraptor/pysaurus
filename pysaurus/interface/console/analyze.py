import math
import sys
from typing import List, Tuple

import ujson as json

from pysaurus.core.profiling import Profiler
from pysaurus.core.video_raptor.alignment_utils import Miniature
from pysaurus.interface.console.compare_images import generate_miniatures
from pysaurus.public.api import API

# r = g = b     ***

# r > g > b     *-_
# r = g > b     **_
# g > r > b     -*_

# g > r = b     _*_

# g > b > r     _*-
# g = b > r     _**
# b > g > r     _-*

# b > g = r     __*

# b > r > g     -_*
# b = r > g     *_*
# r > b > g     *_-

# r > g = b     *__

# [cycle]

PixelTuple = Tuple[float, float, float]
RED, GREEN, BLUE = 0, 1, 2

SIMPLE_MAX_PIXEL_DISTANCE = 255 * 3
V = SIMPLE_MAX_PIXEL_DISTANCE
B = V / 2.0
V_PLUS_B = V + B


def bounds(mu, theta):
    # type: (PixelTuple, PixelTuple) -> Tuple[PixelTuple, PixelTuple]
    return (
        (mu[0] - theta[0], mu[1] - theta[1], mu[2] - theta[2]),
        (mu[0] + theta[0], mu[1] + theta[1], mu[2] + theta[2]),
    )


def moderate(x):
    return V_PLUS_B * x / (x + B)


def pixel_distance(p1, p2):
    return moderate(sum(abs(p1[i] - p2[i]) for i in range(3)))


def pixel_similarity(p1, p2):
    return ((SIMPLE_MAX_PIXEL_DISTANCE - moderate(abs(p1[0] - p2[0]) + abs(p1[1] - p2[1]) + abs(p1[2] - p2[2])))
            / SIMPLE_MAX_PIXEL_DISTANCE)


def pixel_dominance_order(r, g, b):
    if r == g == b: return 0
    if r > g > b: return 1
    if r == g > b: return 2
    if g > r > b: return 3
    if g > r == b: return 4
    if g > b > r: return 5
    if g == b > r: return 6
    if b > g > r: return 7
    if b > g == r: return 8
    if b > r > g: return 9
    if b == r > g: return 10
    if r > b > g: return 11
    if r > g == b: return 12


def compare_pixels(p1, p2, assert_dominance=False):
    dominance_class = pixel_dominance_order(*p1)
    dominance_class_p2 = pixel_dominance_order(*p2)
    t = dominance_class - dominance_class_p2
    if assert_dominance and t:
        raise ValueError('Not same dominance: %d vs %d, %s vs %s' % (dominance_class, dominance_class_p2, p1, p2))
    if t == 0:
        if dominance_class == 0:
            c = [RED]
        elif dominance_class == 1:
            c = [RED, GREEN, BLUE]
        elif dominance_class == 2:
            c = [RED, BLUE]
        elif dominance_class == 3:
            c = [GREEN, RED, BLUE]
        elif dominance_class == 4:
            c = [GREEN, RED]
        elif dominance_class == 5:
            c = [GREEN, BLUE, RED]
        elif dominance_class == 6:
            c = [BLUE, RED]
        elif dominance_class == 7:
            c = [BLUE, GREEN, RED]
        elif dominance_class == 8:
            c = [BLUE, GREEN]
        elif dominance_class == 9:
            c = [BLUE, RED, GREEN]
        elif dominance_class == 10:
            c = [RED, GREEN]
        elif dominance_class == 11:
            c = [RED, BLUE, GREEN]
        elif dominance_class == 12:
            c = [RED, BLUE]
        else:
            raise ValueError('Unknown dominance class %s' % dominance_class)
        for channel in c:
            t = p1[channel] - p2[channel]
            if t != 0:
                break
    return t


def compare_intervals(mu_0, theta_0, mu_1, theta_1):
    # type: (PixelTuple, PixelTuple, PixelTuple, PixelTuple) -> int
    # Same dominance class. Sort by lower bound.
    a_0, b_0 = bounds(mu_0, theta_0)
    a_1, b_1 = bounds(mu_1, theta_1)
    t = compare_pixels(a_0, a_1)
    if not t:
        t = compare_pixels(b_0, b_1)
    return t


def average(miniature):
    # type: (Miniature) -> Tuple[float, float, float]
    return sum(miniature.r) / miniature.size, sum(miniature.g) / miniature.size, sum(miniature.b) / miniature.size


def _standard_deviation(values, mu):
    # type: (List[int], float) -> float
    return math.sqrt(sum((value - mu) * (value - mu) for value in values) / len(values))


def standard_deviation(miniature, mu):
    # type: (Miniature, PixelTuple) -> Tuple[float, float, float]
    mu_r, mu_g, mu_b = mu
    return (
        _standard_deviation(miniature.r, mu_r),
        _standard_deviation(miniature.g, mu_g),
        _standard_deviation(miniature.b, mu_b)
    )


def main():
    discrimination_limit = 0.9
    json_file_name = sys.argv[1]
    with open(json_file_name) as file:
        similarities = json.load(file)
    print('LOADING DATABASE')
    database = API.load_database()
    print('GENERATING MINIATURES')
    miniatures = generate_miniatures(database)
    print(len(miniatures), 'miniatures.')
    print('GENERATING AVERAGES')
    averages = []
    standard_deviations = []
    for miniature in miniatures:
        mu = average(miniature)
        theta = standard_deviation(miniature, mu)
        averages.append(mu)
        standard_deviations.append(theta)
    graph = {}
    nb_miniatures = len(miniatures)
    with Profiler('COMPARING MINIATURES.'):
        for i in range(nb_miniatures):
            for j in range(i + 1, nb_miniatures):
                s = pixel_similarity(averages[i], averages[j])
                if s >= discrimination_limit:
                    s = pixel_similarity(standard_deviations[i], standard_deviations[j])
                    if s >= discrimination_limit:
                        graph.setdefault(i, []).append(j)
                        graph.setdefault(j, []).append(i)
            if i % 500 == 0:
                print('Compared', i + 1, '/', nb_miniatures)
    groups = []
    while graph:
        node_in, linked_nodes = next(iter(graph.items()))
        group = {node_in}
        del graph[node_in]
        while linked_nodes:
            node_out = linked_nodes.pop()
            if node_out not in group:
                group.add(node_out)
                linked_nodes.extend(graph.pop(node_out, []))
        groups.append(sorted(group))
    valid_groups = [group for group in groups if len(group) > 1]
    print('Found', len(groups), 'groups,', len(valid_groups), 'valid groups keeping',
          sum(len(group) for group in valid_groups), '/', len(miniatures), 'miniatures')
    print('Smallest group', min(len(group) for group in valid_groups))
    print('Biggest  group', max(len(group) for group in valid_groups))
    print('Average  group', sum(len(group) for group in valid_groups) / len(valid_groups))
    print('Group    sizes', ', '.join(str(length) for length in sorted(len(group) for group in valid_groups)))
    source_to_group_id = {}
    source_to_index = {}
    for index_group, group in enumerate(valid_groups):
        for index_image in group:
            source_to_group_id[str(miniatures[index_image].identifier)] = index_group
    for i, miniature in enumerate(miniatures):
        source_to_index[str(miniature.identifier)] = i
    print('CHECKING SAVED GROUPS')
    for index_saved, saved_sim_group in enumerate(similarities):
        computed_group = set()
        for saved_source in saved_sim_group:
            computed_group.add(source_to_group_id.get(saved_source, -1))
        if len(computed_group) == 1 and -1 not in computed_group:
            print(index_saved, 'OK')
        else:
            if -1 in computed_group:
                computed_group.remove(-1)
            print(index_saved, '** NOT FOUND **', len(saved_sim_group), 'images in', len(computed_group), 'groups')
            for source, score in saved_sim_group.items():
                print('\t%s\t%s\t%s' % (source_to_group_id.get(source, 'X'), score,
                                        database.get_video_from_filename(source).get_thumbnail_path()))


if __name__ == '__main__':
    main()
