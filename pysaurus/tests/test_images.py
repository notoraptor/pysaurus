import math
import os
from abc import abstractmethod
from multiprocessing import Pool
from typing import List, Tuple, Dict, Set, Any, Union, Iterable, Sequence, Callable

from pysaurus.core import functions
from pysaurus.core.database import notifications
from pysaurus.core.database.api import API
from pysaurus.core.database.video import Video
from pysaurus.core.notification import DEFAULT_NOTIFIER
from pysaurus.core.profiling import Profiler
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH


def _flatten(data: list):
    while isinstance(data[0], list):
        data = [el for seq in data for el in seq]
    return data


def flatten(data: list):
    output = []
    for element in data:
        if isinstance(element, list):
            output.extend(flatten(element))
        else:
            output.append(element)
    return output


def _clip_color(value):
    return min(max(0, value), 255)


def equalize(data):
    if not isinstance(data, (list, tuple)):
        data = list(data)
    grays = sorted({int(sum(p) / 3) for p in data})
    if len(grays) < 2:
        return data
    best_distance = 255 / (len(grays) - 1)
    new_grays = [0]
    for i in range(1, len(grays)):
        new_grays.append(new_grays[i - 1] + best_distance)
    new_grays = [round(gray) for gray in new_grays]
    assert new_grays[-1] == 255, new_grays[-1]
    gray_to_index = {gray: index for index, gray in enumerate(grays)}
    output = []
    for pixel in data:
        r, g, b = pixel
        gray = int((r + g + b) / 3)
        index = gray_to_index[gray]
        new_gray = new_grays[index]
        distance = new_gray - gray
        new_color = _clip_color(r + distance), _clip_color(g + distance), _clip_color(b + distance)
        # assert int(sum(new_color) / 3) == new_gray, (int(sum(new_color) / 3), new_gray, gray, new_color, pixel)
        output.append(new_color)
    return output


class _AbstractPixelComparator:
    __slots__ = ()

    @abstractmethod
    def normalize_data(self, data, width):
        raise NotImplementedError()

    @abstractmethod
    def pixels_are_close(self, data, i, j, width):
        raise NotImplementedError()

    @abstractmethod
    def common_color(self, data, indices, width):
        raise NotImplementedError()


class DistancePixelComparator(_AbstractPixelComparator):
    __slots__ = 'threshold',

    MAX_REAL_DISTANCE = 255 * math.sqrt(3)

    def __pixels_are_close(self, data, i, j, width):
        r1, g1, b1 = data[i]
        r2, g2, b2 = data[j]
        distance = math.sqrt((r1 - r2) * (r1 - r2) + (g1 - g2) * (g1 - g2) + (b1 - b2) * (b1 - b2))
        return distance <= self.threshold * self.MAX_REAL_DISTANCE

    def __init__(self, threshold: Union[int, float]):
        self.threshold = threshold

    def normalize_data(self, data, width):
        return equalize(data)

    def pixels_are_close(self, data, i, j, width):
        return abs(sum(data[i]) - sum(data[j])) <= 3 * 255 * self.threshold

    def common_color(self, data, indices, width):
        sum_r = 0
        sum_g = 0
        sum_b = 0
        for index in indices:
            r, g, b = data[index]
            sum_r += r
            sum_g += g
            sum_b += b
        avg_r = sum_r / len(indices)
        avg_g = sum_g / len(indices)
        avg_b = sum_b / len(indices)
        # return round(avg_r), round(avg_g), round(avg_b)
        return avg_r, avg_g, avg_b


class Graph:
    __slots__ = 'edges',

    def __init__(self):
        self.edges = {}  # type: Dict[Any, Set[Any]]

    def connect(self, a, b):
        self.edges.setdefault(a, set()).add(b)
        self.edges.setdefault(b, set()).add(a)

    def remove(self, a):
        for b in self.edges.pop(a):
            self.edges[b].remove(a)


class BasicGroup:
    __slots__ = 'color', 'center', 'size'

    def __init__(self, color, center, size):
        self.color = color  # type: Tuple[int, int, int]
        self.center = center  # type: Tuple[float, float]
        self.size = size  # type: int

    key = property(lambda self: (self.color, self.center, self.size))
    r = property(lambda self: self.color[0])
    g = property(lambda self: self.color[1])
    b = property(lambda self: self.color[2])
    x = property(lambda self: self.center[0])
    y = property(lambda self: self.center[1])
    s = property(lambda self: self.size)

    def __str__(self):
        return str(self.key)

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return self.key == other.key

    def __lt__(self, other):
        return self.key < other.key


class ValuesAndIndices:
    __slots__ = 'field_to_values', 'field_to_value_to_index'

    def __init__(self, field_to_values, field_to_value_to_index):
        self.field_to_values = field_to_values
        self.field_to_value_to_index = field_to_value_to_index


class Classifier:
    __slots__ = 'field', 'keys', 'values'

    def __init__(self, field=None, keys=None, values=None):
        self.field = field
        self.keys = keys
        self.values = values


DEBUG = False


class GroupClassifier(Classifier):
    __slots__ = ('visitor', 'key_to_index')

    def __init__(self, groups: List[BasicGroup], field: str, constructor=functions.identity):
        clusters = {}
        for group in groups:
            clusters.setdefault(getattr(group, field), []).append(group)
        keys = sorted(clusters)
        super().__init__(field, keys, [constructor(clusters[k]) for k in keys])
        self.visitor = self.visit_one if len(keys) == 1 else self.visit  # type: Callable[[dict], list]
        self.key_to_index = {key: index for index, key in enumerate(self.keys)}

    def compute_local_key_indices(self, vi: ValuesAndIndices):
        # print(self.field, len(self.keys), self.keys[0], self.keys[-1])
        all_keys = vi.field_to_values[self.field]
        if DEBUG:
            print('all keys for', self.field, len(all_keys), all_keys[0], all_keys[-1])
            print('local keys', len(self.keys), self.keys[0], self.keys[-1])
            print('bounds', vi.field_to_value_to_index[self.field][self.keys[0]], vi.field_to_value_to_index[self.field][self.keys[-1]])
            r = list(reversed(range(
                vi.field_to_value_to_index[self.field][self.keys[0]],
                vi.field_to_value_to_index[self.field][self.keys[-1]] + 1
            )))
            if r:
                print('Indices', r[0], r[-1])
                print('Values', all_keys[r[0]], all_keys[r[-1]])
        for i in reversed(range(
            vi.field_to_value_to_index[self.field][self.keys[0]],
            vi.field_to_value_to_index[self.field][self.keys[-1]] + 1
        )):
            if all_keys[i] not in self.key_to_index:
                self.key_to_index[all_keys[i]] = self.key_to_index[all_keys[i + 1]]

    def count_children(self):
        return len(self.values) + sum(v.count_children() for v in self.values)

    def collect_children(self, output):
        output.extend(self.values)
        for v in self.values:
            v.collect_children(output)

    def count(self):
        return 1 + self.count_children()

    def collect(self):
        output = [self]
        self.collect_children(output)
        return output

    @classmethod
    def builder(cls, field, constructor=functions.identity):
        return lambda groups: cls(groups, field, constructor)

    def visit(self, field_to_bounds):
        start, end = field_to_bounds[self.field]
        return [self.values[i].visitor(field_to_bounds)
                for i in range(functions.get_start_index(self.keys, start), functions.get_end_index(self.keys, end))]

    def visit_one(self, field_to_bounds):
        start, end = field_to_bounds[self.field]
        return self.values[0].visitor(field_to_bounds) if start <= self.keys[0] <= end else []


class LeafGroupClassifier(GroupClassifier):
    __slots__ = ()

    def count_children(self):
        return 0

    def collect_children(self, output):
        pass

    def visit(self, field_to_bounds):
        start, end = field_to_bounds[self.field]
        return self.values[functions.get_start_index(self.keys, start):functions.get_end_index(self.keys, end)]

    def visit_one(self, field_to_bounds):
        start, end = field_to_bounds[self.field]
        return self.values[0] if start <= self.keys[0] <= end else []


class PixelGroup:
    __slots__ = 'color', 'image_width', 'identifier', 'members', 'connections'

    def __init__(self, color: Tuple[float, float, float], image_width: int, identifier: int, members: Set[int]):
        self.color = color
        self.image_width = image_width
        self.identifier = identifier
        self.members = members
        self.connections = set()  # type: Set[PixelGroup]

    def __str__(self):
        return (
            f"PixelGroup({self.identifier + 1} "
            f"{self.color}, "
            f"{len(self.members)} member{functions.get_plural_suffix(len(self.members))}, "
            f"center {self.center}, "
            f"{len(self.connections)} connection{functions.get_plural_suffix(len(self.connections))})"
        )

    def __hash__(self):
        return hash(self.identifier)

    def __eq__(self, other):
        return self.identifier == other.identifier

    def to_basic_group(self):
        return BasicGroup(self.color, self.center, len(self.members))

    @property
    def center(self):
        nb_points = len(self.members)
        total_x = 0
        total_y = 0
        for identifier in self.members:
            x, y = functions.flat_to_coord(identifier, self.image_width)
            total_x += x
            total_y += y
        return total_x / nb_points, total_y / nb_points


class LinearFunction:
    __slots__ = 'a', 'b'

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __str__(self):
        return f"(x: {self.a}*x {'' if self.b < 0 else '+'}{self.b})"

    def __call__(self, x):
        return self.a * x + self.b

    def latest_intersection(self, values: List[Union[int, float]]):
        n = len(values)
        y_values = sorted(values)
        direction = None
        for i in range(n):
            x = n - i - 1
            v = y_values[x]
            y = self(x)
            if v == y:
                print('Stopped from behind (==) at', i + 1, '/', len(values))
                return v
            current_direction = v > y
            if direction is None:
                direction = current_direction
            elif direction is not current_direction:
                print('Stopped from behind (!=) at', i + 1, '/', len(values))
                return v
        raise ValueError(f'Unable to get latest intersection {self} from {[self(c) for c in range(n)]} to {y_values}')

    @classmethod
    def get_linear_regression(cls, values: list):
        n = len(values)
        y_values = sorted(values)
        x_values = list(range(n))
        average_x = sum(x_values) / n
        average_y = sum(y_values) / n
        var_x = (sum(x ** 2 for x in x_values) / n) - average_x ** 2
        cov_xy = (sum(x * y for x, y in zip(x_values, y_values)) / n) - average_x * average_y
        a = cov_xy / var_x
        b = average_y - a * average_x
        return LinearFunction(a, b)

    @classmethod
    def get_line(cls, x1, y1, x2, y2):
        a = (y2 - y1) / (x2 - x1)
        b = y1 - a * x1
        return LinearFunction(a, b)


class AxeGroup:
    __slots__ = 'name', 'values', 'columns'
    __fields__ = ('r', 'g', 'b', 'x', 'y', 's',)

    def __init__(self, name, values: List[Any], columns: List[List[BasicGroup]]):
        self.name = name
        self.values = values
        self.columns = columns

    def divide(self, limit) -> List[List[BasicGroup]]:
        new_clusters = []  # type: List[List[BasicGroup]]
        cursor = 0
        for i in range(1, len(self.values)):
            if self.values[i] - self.values[i - 1] > limit:
                new_cluster = []
                for column in self.columns[cursor: i]:
                    new_cluster += column
                new_clusters.append(new_cluster)
                cursor = i
        last_cluster = []
        for elements in self.columns[cursor:]:
            last_cluster += elements
        new_clusters.append(last_cluster)
        return [c for c in new_clusters if len(c) > 1]

    @classmethod
    def is_valid(cls, groups, field):
        if isinstance(groups, cls):
            if groups.name != field:
                raise ValueError(f'Expected axe group for field {field}, got {groups.name}')
            return True
        return False

    @classmethod
    def list(cls, clusters: List[List[BasicGroup]], field):
        return [(groups if cls.is_valid(groups, field) else cls.to_group(field, groups)) for groups in clusters]

    @classmethod
    def to_group(cls, name, groups: List[BasicGroup]):
        classifier = {}
        for group in groups:
            classifier.setdefault(getattr(group, name), []).append(group)
        return cls.already_grouped(name, classifier)

    @classmethod
    def already_grouped(cls, name, classifier: Dict[Any, List[BasicGroup]]):
        values = []
        columns = []
        for value in sorted(classifier):
            values.append(value)
            columns.append(classifier[value])
        return cls(name, values, columns)


LENGTH = 256
NB_POINTS = 6
THRESHOLD = 0.5
MIN_COUNT = 10
GROUP_MIN_SIZE = 4
PIXEL_COMPARATOR = DistancePixelComparator(0.0125)


def group_pixels(raw_data, width, height) -> List[PixelGroup]:
    data = PIXEL_COMPARATOR.normalize_data(raw_data, width)
    graph = Graph()
    disconnected = Graph()
    # Connect pixels in first line.
    for current_index in range(1, width):
        previous_index = current_index - 1
        if PIXEL_COMPARATOR.pixels_are_close(data, current_index, previous_index, width):
            graph.connect(current_index, previous_index)
        else:
            disconnected.connect(current_index, previous_index)
    # Connect pixels in next lines.
    for y in range(1, height):
        # Connect first pixel.
        current_index = y * width
        above_index = current_index - width
        if PIXEL_COMPARATOR.pixels_are_close(data, current_index, above_index, width):
            graph.connect(current_index, above_index)
        else:
            disconnected.connect(current_index, above_index)
        # Connect next pixels.
        for x in range(1, width):
            current_index = y * width + x
            above_index = current_index - width
            previous_index = current_index - 1
            top_left_index = current_index - width - 1
            if PIXEL_COMPARATOR.pixels_are_close(data, current_index, above_index, width):
                graph.connect(current_index, above_index)
            else:
                disconnected.connect(current_index, above_index)
            if PIXEL_COMPARATOR.pixels_are_close(data, current_index, previous_index, width):
                graph.connect(current_index, previous_index)
            else:
                disconnected.connect(current_index, previous_index)
            if PIXEL_COMPARATOR.pixels_are_close(data, current_index, top_left_index, width):
                graph.connect(current_index, top_left_index)
            else:
                disconnected.connect(current_index, top_left_index)
    # Get groups and connect each pixel to its group.
    groups = []  # type: List[PixelGroup]
    _ungrouped_indices = set(range(width * height))  # type: Set[int]
    _index_to_group = {}  # type: Dict[int, int]
    while graph.edges:
        index, other_indices = graph.edges.popitem()
        group_id = len(groups)
        group = {index}
        _index_to_group[index] = group_id
        _ungrouped_indices.remove(index)
        while other_indices:
            other_index = other_indices.pop()
            if other_index not in group:
                group.add(other_index)
                other_indices.update(graph.edges.pop(other_index))
                _index_to_group[other_index] = group_id
                _ungrouped_indices.remove(other_index)
        groups.append(PixelGroup(PIXEL_COMPARATOR.common_color(data, group, width), width, group_id, group))
    for ungrouped_index in _ungrouped_indices:
        disconnected.remove(ungrouped_index)
    # Connect groups.
    for in_index, out_indices in disconnected.edges.items():
        id_group_in = _index_to_group[in_index]
        for out_index in out_indices:
            if id_group_in != _index_to_group[out_index]:
                groups[id_group_in].connections.add(groups[_index_to_group[out_index]])
    return groups


def compute_groups(data: Iterable[Tuple[int, int, int]], width: int, height: int) -> List[BasicGroup]:
    return [group.to_basic_group()
            for group in group_pixels(data, width, height)
            if len(group.members) >= GROUP_MIN_SIZE]


def _info_final_clusters(final_clusters: List[List[BasicGroup]], names):
    for i, cluster in enumerate(sorted(final_clusters, key=lambda c: len(c))):  # type: List[BasicGroup]
        it_clus = iter(cluster)
        g = next(it_clus)
        minimums = {name: getattr(g, name) for name in names}
        maximums = {name: getattr(g, name) for name in names}
        for group in it_clus:
            for name in names:
                minimums[name] = min(minimums[name], getattr(group, name))
                maximums[name] = max(maximums[name], getattr(group, name))
        print('Cluster', i + 1, 'size', len(cluster))
        for name in names:
            min_v = minimums[name]
            max_v = maximums[name]
            print(f'\t{name}: min {min_v} max {max_v} diff {max_v - min_v}')


def _info_final_videos(final_videos, video_to_groups):
    for i, (path, groups) in enumerate(sorted(final_videos.items())):
        print(f'[{i + 1}] {path}')
        print(
            f'\tfinal: {len(groups)},',
            f'initial: {len(video_to_groups[path])},',
            f'rate {len(groups) * 100 / len(video_to_groups[path])} %,',
            f'groups: {", ".join(str(g) for g in sorted(groups))}'
        )


def _sub_clusterize(groups: List[BasicGroup], name) -> List[List[BasicGroup]]:
    axe = {}
    for group in groups:
        axe.setdefault(getattr(group, name), []).append(group)
    return [axe[value] for value in sorted(axe)]


def clusterize(limits: Dict[str, float],
               clusters: List[List[BasicGroup]],
               names: List[str],
               index_name: int,
               output: List[List[BasicGroup]]) -> None:
    name = names[index_name]
    limit = limits[name]
    new_clusters = []  # type: List[List[BasicGroup]]
    cursor = 0
    for i in range(1, len(clusters)):
        value_prev = getattr(clusters[i - 1][0], name)
        value_curr = getattr(clusters[i][0], name)
        if value_curr - value_prev > limit:
            new_cluster = []
            for elements in clusters[cursor: i]:
                new_cluster += elements
            new_clusters.append(new_cluster)
            cursor = i
    last_cluster = []
    for elements in clusters[cursor:]:
        last_cluster += elements
    new_clusters.append(last_cluster)
    new_clusters = [c for c in new_clusters if len(c) > 1]

    if index_name == len(names) - 1:
        output.extend(new_clusters)
        return
    next_name = names[index_name + 1]
    for cluster in new_clusters:
        sub_clusters = _sub_clusterize(cluster, next_name)
        clusterize(limits, sub_clusters, names, index_name + 1, output)


def get_clusters(limits: Dict[str, float], groups: Union[AxeGroup, List[BasicGroup]]):
    clusters = [groups]
    for field in AxeGroup.__fields__:
        if field in limits:
            axe_groups = AxeGroup.list(clusters, field)
            divided_clusters = []  # type: List[List[BasicGroup]]
            for axe_group in axe_groups:
                divided_clusters += axe_group.divide(limits[field])
            print(field, 'before', len(clusters), 'after', len(divided_clusters))
            clusters = divided_clusters
    return clusters


def compute_expected_value(values):
    total = sum(values)
    unique_values = {}
    for value in values:
        unique_values[value] = unique_values.get(value, 0) + 1
    return sum(
        nb_value * value * value / total
        for value, nb_value in unique_values.items()
    )


def analyze_groups(groups: List[BasicGroup]) -> List[List[BasicGroup]]:
    axes = {field: {} for field in AxeGroup.__fields__}  # type: Dict[str, Dict[Any, List[BasicGroup]]]
    limits = {}
    for group in groups:
        for field in AxeGroup.__fields__:
            axes[field].setdefault(getattr(group, field), []).append(group)
    for name, axe in axes.items():
        if len(axe) < 2:
            print(f'Axe {name} has only {len(axe)} values')
            continue
        values = sorted(axe)
        min_d = max_d = values[1] - values[0]
        distances = [min_d]
        for i in range(2, len(values)):
            d = values[i] - values[i - 1]
            min_d = min(min_d, d)
            max_d = max(max_d, d)
            distances.append(d)
        assert len(distances) == len(values) - 1
        distances.sort()
        if len(distances) % 2:
            median = distances[len(distances) // 2]
        else:
            median = (distances[len(distances) // 2 - 1] + distances[len(distances) // 2]) / 2
        average = sum(distances) / (len(values) - 1)
        # fn = LinearFunction.get_linear_regression(distances)
        fn = LinearFunction.get_line(0, distances[0], len(distances) - 1, distances[-1] / 2)
        expected_value = compute_expected_value(distances)
        index_exp = functions.get_end_index(distances, expected_value)
        print('Exp at', len(distances) - index_exp, '/', len(distances))
        # limit = distances[int(9 * len(distances) / 10)]
        # limit = expected_value
        limit = fn.latest_intersection(distances)
        limits[name] = limit
        print(f'{name} ({len(axe)}):')
        print(f'\t[{min_d} ... {median} ... {max_d}]')
        print(f'\tAverage:', average)
        print(f'\tExpected:', expected_value)
        print(f'\tLimit:', limit)
        print(f'\tf(x) =', fn)
        print(f'\tf(0) =', fn(0))
        print(f'\tf(#) =', fn(len(distances) - 1))
    names = list(AxeGroup.__fields__)
    axe = axes[names[0]]
    clusters = [axe[value] for value in sorted(axe)]
    final_clusters = []
    with Profiler('Clusterize'):
        clusterize(limits, clusters, names, 0, final_clusters)
    with Profiler('Clusterize | new version'):
        get_clusters(limits, AxeGroup.already_grouped(names[0], axe))
    print('Final clusters', len(final_clusters))
    print('Min size', min(len(c) for c in final_clusters))
    print('Max size', max(len(c) for c in final_clusters))
    print('Total size', sum(len(c) for c in final_clusters))
    print('Initial size', len(groups))

    return final_clusters


DEC_R = DEC_G = DEC_B = 2
DEC_X = DEC_Y = 0.5
DEC_S = 4
DEC = {
    'r': DEC_R,
    'g': DEC_G,
    'b': DEC_B,
    'x': DEC_X,
    'y': DEC_Y,
    's': DEC_S,
}

FIELDS = ('r', 'g', 'b', 'x', 'y', 's')


def compute_indices(groups: List[BasicGroup]):
    field_to_values = {}
    field_to_value_to_index = {}
    for f in FIELDS:
        dec = DEC[f]
        values = [getattr(g, f) for g in groups]
        v_less = [v - dec for v in values]
        v_more = [v + dec for v in values]
        field_values = list(set(values + v_less + v_more))
        field_values.sort()
        field_to_values[f] = field_values
        field_to_value_to_index[f] = {value: index for index, value in enumerate(field_values)}
    return ValuesAndIndices(field_to_values, field_to_value_to_index)


CLASSIFIER_CONSTRUCTOR = GroupClassifier.builder(
    'r', GroupClassifier.builder(
        'g', GroupClassifier.builder(
            'b', GroupClassifier.builder(
                'x', GroupClassifier.builder(
                    'y', LeafGroupClassifier.builder(
                        's'))))))


def analyze_groups_2(groups: List[BasicGroup]):
    with Profiler('Classify groups'):
        classifier = CLASSIFIER_CONSTRUCTOR(groups)
    with Profiler('Count non-leaf nodes'):
        nb_nodes = classifier.count()
        print(nb_nodes)
    with Profiler('Collect all nodes'):
        nodes = classifier.collect()
        assert len(nodes) == nb_nodes, (len(nodes), nb_nodes)
    with Profiler('Compute all values and indices'):
        vi = compute_indices(groups)
    with Profiler('Select optimizable nodes'):
        opt_nodes = [c for c in nodes if len(c.keys) > 1]
        print(len(opt_nodes))
    with Profiler('Compute all key indices'):
        for i, c in enumerate(opt_nodes):
            c.compute_local_key_indices(vi)
            if i % 1000 == 0:
                print(i + 1, '/', len(opt_nodes))
    return
    # with Profiler('Compute all key indices'):
    #     classifier.compute_key_indices(vi)
    # cpu_count = max(1, os.cpu_count() - 2)
    test_size = 10000
    with Profiler(f'Get similar groups for {test_size} groups'):
        for i, group in enumerate(groups[:test_size]):
            near = classifier.visitor({
                'r': (group.color[0] - DEC_R, group.color[0] + DEC_R),
                'g': (group.color[1] - DEC_G, group.color[1] + DEC_G),
                'b': (group.color[2] - DEC_B, group.color[2] + DEC_B),
                'x': (group.center[0] - DEC_X, group.center[0] + DEC_X),
                'y': (group.center[1] - DEC_Y, group.center[1] + DEC_Y),
                's': (group.size - DEC_S, group.size + DEC_S)
            })
            if i % 1000 == 0:
                print('Group', i, 'similar', len(flatten(near)))


def async_compute_groups(context):
    i, m, t, n = context
    if (i + 1) % 1000 == 0:
        n.notify(notifications.VideoJob('', i + 1, t))
    return m.identifier, compute_groups(m.data(), m.width, m.height)


def main():
    cpu_count = max(1, os.cpu_count() - 2)
    api = API(TEST_LIST_FILE_PATH, update=False)
    videos = list(api.database.readable.found.with_thumbnails) + list(
        api.database.readable.not_found.with_thumbnails)  # type: List[Video]
    # videos_dict = {v.filename.path: v for v in videos}  # type: Dict[str, Video]
    min_dict = {m.identifier: m for m in api.database.ensure_miniatures(return_miniatures=True)}
    miniatures = [min_dict[video.filename.path] for video in videos]
    tasks = [(i, m, len(miniatures), DEFAULT_NOTIFIER) for i, m in enumerate(miniatures)]

    with Profiler(f'Segment {len(tasks)} videos.'):
        with Pool(cpu_count) as p:
            output = list(p.imap(async_compute_groups, tasks))
    DEFAULT_NOTIFIER.notify(notifications.VideoJob('', len(miniatures), len(miniatures)))
    assert len(output) == len(tasks), (len(output), len(tasks))

    it_output = iter(output)
    p, ig = next(it_output)
    min_g = max_g = len(ig)
    all_groups = ig
    video_to_groups = {p: ig}
    group_to_video = {g: p for g in ig}
    for path, image_groups in it_output:
        min_g = min(min_g, len(image_groups))
        max_g = max(max_g, len(image_groups))
        all_groups += image_groups
        video_to_groups[path] = image_groups
        for g in image_groups:
            group_to_video[g] = path
    avg_g = len(all_groups) / len(output)
    print('Min group size', min_g)
    print('Max group size', max_g)
    print('Total groups', len(all_groups))
    print('Average group size', avg_g)
    for path, groups in video_to_groups.items():
        if len(groups) == min_g:
            print('Min', path)
        if len(groups) == max_g:
            print('Max', path)
    return analyze_groups_2(all_groups)
    clusters = analyze_groups(all_groups)
    retained_videos = {}
    retained_len = {}
    for i, cluster in enumerate(clusters):
        for group in cluster:
            path = group_to_video[group]
            retained_videos.setdefault(path, []).append(i)
            retained_len[path] = retained_len.get(path, 0) + group.size
    final_videos = {path: groups for path, groups in retained_videos.items() if
                    retained_len[path] >= 50 * sum(g.size for g in video_to_groups[path]) / 100}
    print('Retained videos', len(retained_videos))
    print('Final videos', len(final_videos))


if __name__ == '__main__':
    with Profiler('MAIN'):
        main()
