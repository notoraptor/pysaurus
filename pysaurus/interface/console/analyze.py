import functools
import math
import sys
from typing import List, Tuple, Optional

import ujson as json

from pysaurus.core.video_raptor.alignment_utils import Miniature
from pysaurus.interface.console.compare_images import generate_miniatures
from pysaurus.public.api import API
from pysaurus.core.profiling import Profiler

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
    sum_r = 0
    sum_g = 0
    sum_b = 0
    for r, g, b in miniature.tuples():
        sum_r += r
        sum_g += g
        sum_b += b
    return sum_r / miniature.size, sum_g / miniature.size, sum_b / miniature.size


def standard_deviation(miniature, mu):
    # type: (Miniature, PixelTuple) -> Tuple[float, float, float]
    mu_r, mu_g, mu_b = mu
    sum_r = 0
    sum_g = 0
    sum_b = 0
    for r, g, b in miniature.tuples():
        sum_r += (r - mu_r) * (r - mu_r)
        sum_g += (g - mu_g) * (g - mu_g)
        sum_b += (b - mu_b) * (b - mu_b)
    return math.sqrt(sum_r / miniature.size), math.sqrt(sum_g / miniature.size), math.sqrt(sum_b / miniature.size)


def main():
    sim_limit = 0.9
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
    print('SORTING MINIATURES')
    nb_miniatures = len(miniatures)
    classes = list(range(nb_miniatures))
    scores = [0] * nb_miniatures
    with Profiler('Comparing miniatures.'):
        for i in range(nb_miniatures):
            for j in range(i + 1, nb_miniatures):
                s = pixel_similarity(averages[i], averages[j])
                if s >= sim_limit and s > scores[j]:
                    s = pixel_similarity(standard_deviations[i], standard_deviations[j])
                    if s >= sim_limit and s > scores[j]:
                        classes[j] = classes[i]
                        scores[j] = s
            if i % 500 == 0:
                print('Compared', i + 1, '/', nb_miniatures)
    groups = {}
    for index_image, group_id in enumerate(classes):
        groups.setdefault(group_id, []).append(index_image)
    valid_groups = [group for group in groups.values() if len(group) > 1]
    print('Found', len(groups), 'groups,', len(valid_groups), 'valid groups, in', len(miniatures), 'miniatures')
    source_to_group_id = {}
    source_to_miniature = {}
    source_to_index = {}
    for index_group, group in enumerate(valid_groups):
        for index_image in group:
            source_to_group_id[str(miniatures[index_image].identifier)] = index_group
    for i, miniature in enumerate(miniatures):
        source_to_miniature[str(miniature.identifier)] = miniature
        source_to_index[str(miniature.identifier)] = i
    print('CHECKING SAVED GROUPS')
    for index_saved, saved_sim_group in enumerate(similarities):
        computed_group = set()
        for saved_source in saved_sim_group:
            computed_group.add(source_to_group_id.get(saved_source, -1))
        if len(computed_group) == 1 and -1 not in computed_group:
            print(index_saved, 'OK')
        else:
            remaining_sources = []
            mus = []
            thetas = []
            mu_sims = []
            theta_sims = []
            for saved_source in saved_sim_group:
                mu = averages[source_to_index[saved_source]]
                theta = standard_deviations[source_to_index[saved_source]]
                if not remaining_sources:
                    remaining_sources.append(saved_source)
                    mus.append(mu)
                    thetas.append(theta)
                    mu_sims.append(1)
                    theta_sims.append(1)
                    continue
                mu_sim = pixel_similarity(mu, mus[0])
                theta_sim = pixel_similarity(theta, thetas[0])
                if mu_sim >= sim_limit and theta_sim >= sim_limit:
                    remaining_sources.append(saved_source)
                    mus.append(mu)
                    thetas.append(theta)
                    mu_sims.append(mu_sim)
                    theta_sims.append(theta_sim)
            if len(remaining_sources) == 1:
                print(index_saved, 'OK (only 1 remaining image after removing weak links)')
            else:
                print(index_saved, '** NOT FOUND **',
                      '[%d images in %d groups]. Strong ones:' % (len(saved_sim_group), len(computed_group)),
                      ', '.join(str(i) for i in computed_group))
                for i in range(len(remaining_sources)):
                    print('\t%s' % database.get_video_from_filename(remaining_sources[i]).get_thumbnail_path(database.folder))
                    print('\t%s\t%s' % (mus[i], thetas[i]))
                    print('\t%s\t%s' % (mu_sims[i], theta_sims[i]))

if __name__ == '__main__':
    main()
