from pysaurus.core.video_raptor.alignment_utils import Miniature
from pysaurus.core.utils.functions import generate_amplifier_function
from pysaurus.public.api import API
from pysaurus.interface.console.compare_images import generate_miniatures


SIMPLE_MAX_PIXEL_DISTANCE = 255 * 3

WIDTH = 1
HEIGHT = 1
MAXIMUM_SIMILARITY_SCORE = SIMPLE_MAX_PIXEL_DISTANCE * WIDTH * HEIGHT
V = SIMPLE_MAX_PIXEL_DISTANCE
B = V / 2.0


moderate = generate_amplifier_function(V, B)


def pixel_distance(p1, x, y, p2, localX, localY, width):
    # type: (Miniature, int, int, Miniature, int, int, int) -> float
    indexP1 = x + y * width
    indexP2 = localX + localY * width
    return moderate(
        abs(p1.r[indexP1] - p2.r[indexP2])
        + abs(p1.g[indexP1] - p2.g[indexP2])
        + abs(p1.b[indexP1] - p2.b[indexP2]))


def compare(p1, p2):
    # type: (Miniature, Miniature) -> float
    width = p1.width
    height = p1.height
    maximum_similarity_score = SIMPLE_MAX_PIXEL_DISTANCE * width * height
    # x, y:
    # 0, 0
    total_distance = min(
        pixel_distance(p1, 0, 0, p2, 0, 0, width),
        pixel_distance(p1, 0, 0, p2, 1, 0, width),
        pixel_distance(p1, 0, 0, p2, 0, 1, width),
        pixel_distance(p1, 0, 0, p2, 1, 1, width))
    # width - 1, 0
    total_distance += min(
        pixel_distance(p1, width - 1, 0, p2, width - 2, 0, width),
        pixel_distance(p1, width - 1, 0, p2, width - 1, 0, width),
        pixel_distance(p1, width - 1, 0, p2, width - 2, 1, width),
        pixel_distance(p1, width - 1, 0, p2, width - 1, 1, width))
    # 0, height - 1
    total_distance += min(
        pixel_distance(p1, 0, height - 1, p2, 0, height - 1, width),
        pixel_distance(p1, 0, height - 1, p2, 1, height - 1, width),
        pixel_distance(p1, 0, height - 1, p2, 0, height - 2, width),
        pixel_distance(p1, 0, height - 1, p2, 1, height - 2, width))
    # width - 1, height - 1
    total_distance += min(
        pixel_distance(p1, width - 1, height - 1, p2, width - 2, height - 1, width),
        pixel_distance(p1, width - 1, height - 1, p2, width - 1, height - 1, width),
        pixel_distance(p1, width - 1, height - 1, p2, width - 2, height - 2, width),
        pixel_distance(p1, width - 1, height - 1, p2, width - 1, height - 2, width))
    # x, 0
    for x in range(1, width - 1):
        total_distance += min(
            pixel_distance(p1, x, 0, p2, x - 1, 0, width),
            pixel_distance(p1, x, 0, p2, x, 0, width),
            pixel_distance(p1, x, 0, p2, x + 1, 0, width),
            pixel_distance(p1, x, 0, p2, x - 1, 1, width),
            pixel_distance(p1, x, 0, p2, x, 1, width),
            pixel_distance(p1, x, 0, p2, x + 1, 1, width))
    # x, height - 1
    for x in range(1, width - 1):
        total_distance += min(
            pixel_distance(p1, x, height - 1, p2, x - 1, height - 1, width),
            pixel_distance(p1, x, height - 1, p2, x, height - 1, width),
            pixel_distance(p1, x, height - 1, p2, x + 1, height - 1, width),
            pixel_distance(p1, x, height - 1, p2, x - 1, height - 2, width),
            pixel_distance(p1, x, height - 1, p2, x, height - 2, width),
            pixel_distance(p1, x, height - 1, p2, x + 1, height - 2, width))
    for y in range(1, height - 1):
        # 0, y
        total_distance += min(
            pixel_distance(p1, 0, y, p2, 0, y - 1, width),
            pixel_distance(p1, 0, y, p2, 1, y - 1, width),
            pixel_distance(p1, 0, y, p2, 0, y, width),
            pixel_distance(p1, 0, y, p2, 1, y, width),
            pixel_distance(p1, 0, y, p2, 0, y + 1, width),
            pixel_distance(p1, 0, y, p2, 1, y + 1, width))
        # width - 1, y
        total_distance += min(
            pixel_distance(p1, width - 1, y, p2, width - 2, y - 1, width),
            pixel_distance(p1, width - 1, y, p2, width - 1, y - 1, width),
            pixel_distance(p1, width - 1, y, p2, width - 2, y, width),
            pixel_distance(p1, width - 1, y, p2, width - 1, y, width),
            pixel_distance(p1, width - 1, y, p2, width - 2, y + 1, width),
            pixel_distance(p1, width - 1, y, p2, width - 1, y + 1, width))
    # x in [1; width - 2], y in [1; height - 2]
    remaining_size = (width - 2) * (height - 2)
    for index in range(0, remaining_size):
        x = index % (width - 2) + 1
        y = int(index / (width - 2)) + 1
        total_distance += min(
            pixel_distance(p1, x, y, p2, x - 1, y - 1, width),
            pixel_distance(p1, x, y, p2, x, y - 1, width),
            pixel_distance(p1, x, y, p2, x + 1, y - 1, width),
            pixel_distance(p1, x, y, p2, x - 1, y, width),
            pixel_distance(p1, x, y, p2, x, y, width),
            pixel_distance(p1, x, y, p2, x + 1, y, width),
            pixel_distance(p1, x, y, p2, x - 1, y + 1, width),
            pixel_distance(p1, x, y, p2, x, y + 1, width),
            pixel_distance(p1, x, y, p2, x + 1, y + 1, width))
    return (maximum_similarity_score - total_distance) / maximum_similarity_score


def extract_linked_nodes(graph):
    # type: (dict) -> list
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
    return groups


def main():
    sim_limit = 0.9
    print('LOADING DATABASE')
    database = API.load_database()
    print('GENERATING MINIATURES')
    miniatures = generate_miniatures(database)
    nb_miniatures = len(miniatures)
    print(nb_miniatures, 'miniatures.')
    print('COMPARING FIRST MINIATURE TO ALL OTHERS')
    first_group = []
    comparison_graph = {}
    scores = []
    miniature_0 = miniatures[0]
    for i in range(1, nb_miniatures):
        score = compare(miniature_0, miniatures[i])
        if score >= sim_limit:
            first_group.append(i)
        scores.append((score, i))
        if i % 100 == 0:
            print(i + 1, '/', nb_miniatures)
    print('GENERATING FIRST COMPARISON GROUPS')
    scores.sort()
    print(scores[:10])
    start = 0
    for start in range(len(scores)):
        score_0, index_0 = scores[start]
        for cursor in range(start + 1, len(scores)):
            score_i, index_i = scores[cursor]
            if 1 - abs(score_0 - score_i) >= sim_limit:
                comparison_graph.setdefault(index_0, []).append(index_i)
                comparison_graph.setdefault(index_i, []).append(index_0)
            else:
                print(start, cursor - start)
                break
    groups = extract_linked_nodes(comparison_graph)
    valid_groups = [g for g in groups if len(g) > 1]
    print(len(valid_groups), 'comparison groups')
    if len(valid_groups):
        print(min(len(g) for g in valid_groups), 'minimum size')
        print(max(len(g) for g in valid_groups), 'maximum size')
        print(sum(len(g) for g in valid_groups)/len(valid_groups), 'average size')


if __name__ == '__main__':
    main()
