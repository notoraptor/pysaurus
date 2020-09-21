import math
import os
from abc import abstractmethod
from ast import literal_eval
from multiprocessing import Pool
from typing import List, Tuple, Dict, Set, Any, Union, Iterable

from pysaurus.core import functions
from pysaurus.core.database import notifications
from pysaurus.core.database.api import API
from pysaurus.core.database.properties import PropType
from pysaurus.core.database.video import Video
from pysaurus.core.modules import Color, Workspace
from pysaurus.core.notification import DEFAULT_NOTIFIER
from pysaurus.core.profiling import Profiler
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH


def _space_between_points(interval_length, nb_points):
    # 2 <= k < interval_length
    top = interval_length - nb_points
    bottom = nb_points - 1
    if top % (2 * bottom):
        return None
    return top // bottom


def _available_points_and_spaces(interval_length):
    pt_to_il = {}
    for pt in range(2, interval_length):
        il = _space_between_points(interval_length, pt)
        if il:
            pt_to_il[pt] = il
    return pt_to_il


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


class SpacedPoints:
    """
    for interval length = 256, we have available points:
    k = 2;  c = 8;      l = 254
    k = 4;  c = 64;     l = 84
    k = 6;  c = 216;    l = 50
    k = 16; c = 4096;   l = 16
    k = 18; c = 5832;   l = 14
    k = 52; c = 140608; l = 4
    k = 86; c = 636056; l = 2
    """

    __slots__ = 'd', 'index_of', 'near_indices_of'
    _MAP_POINTS = {}

    def __init__(self, length=256, nb_points=6):
        if length not in self._MAP_POINTS:
            self._MAP_POINTS[length] = _available_points_and_spaces(length)
        points = self._MAP_POINTS[length]
        assert nb_points in points, tuple(points)
        self.d = points[nb_points] + 1
        self.index_of = [self.nearest_index(value) for value in range(length)]
        self.near_indices_of = [self.nearest_indices(value, length) for value in range(length)]

    def nearest_index(self, value: Union[int, float]):
        # 0 <= value < interval length
        i = int(value // self.d)
        before = i * self.d
        after = (i + 1) * self.d
        if value - before < after - value:
            return i
        return i + 1

    def nearest_indices(self, value: Union[int, float], length):
        return sorted({
            self.nearest_index(max(0, value - (self.d - 1) // 2)),
            self.nearest_index(value),
            self.nearest_index(min(length - 1, value + (self.d - 1) // 2))
        })

    def nearest_point(self, value: Union[int, float]):
        # 0 <= value < interval length
        i = int(value // self.d)
        before = i * self.d
        after = (i + 1) * self.d
        if value - before < after - value:
            return before
        return after

    def nearest_points(self, values: Union[list, tuple]):
        return type(values)(self.nearest_point(value) for value in values)


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


class PixelComparator(_AbstractPixelComparator):
    __slots__ = 'spaced_points',

    def __init__(self, spaced_points: SpacedPoints):
        self.spaced_points = spaced_points

    def normalize_data(self, data, width):
        return [self.spaced_points.nearest_points(pixel) for pixel in data]

    def pixels_are_close(self, data, i, j, width):
        return data[i] == data[j]

    def common_color(self, data, indices, width):
        return data[next(iter(indices))]


class DistancePixelComparator(_AbstractPixelComparator):
    __slots__ = 'threshold', 'spaced_points'

    MAX_REAL_DISTANCE = 255 * math.sqrt(3)

    def __init__(self, threshold: Union[int, float], spaced_points: SpacedPoints):
        self.threshold = threshold
        self.spaced_points = spaced_points

    def normalize_data(self, data, width):
        return equalize(data)

    def pixels_are_close(self, data, i, j, width):
        return abs(sum(data[i]) - sum(data[j])) <= 3 * 255 * self.threshold

    def _pixels_are_close(self, data, i, j, width):
        r1, g1, b1 = data[i]
        r2, g2, b2 = data[j]
        distance = math.sqrt((r1 - r2) * (r1 - r2) + (g1 - g2) * (g1 - g2) + (b1 - b2) * (b1 - b2))
        return distance <= self.threshold * self.MAX_REAL_DISTANCE

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
        return round(avg_r), round(avg_g), round(avg_b)


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


class PixelGroup:
    __slots__ = 'real_color', 'color', 'image_width', 'identifier', 'members', 'connections'

    def __init__(self, color: Tuple[int, int, int], image_width: int, identifier: int, members: Set[int]):
        self.real_color = color
        self.color = (
            SPACED_POINTS.index_of[color[0]],
            SPACED_POINTS.index_of[color[1]],
            SPACED_POINTS.index_of[color[2]],
        )
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


def categorize_angle(degrees):
    """Return nearest multiple of 45 degrees to given degrees."""
    index_before = int(degrees // 45)
    angle_before = index_before * 45
    angle_after = (index_before + 1) * 45
    if (degrees - angle_before) < (angle_after - degrees):
        return angle_before
    return angle_after % 360


INDEX_OF = [categorize_angle(angle) for angle in range(360)]
NEAR_INDICES_OF = [sorted({
    categorize_angle(max(0, angle - 22)),
    categorize_angle(angle),
    categorize_angle(min(360, angle + 22) % 360)
}) for angle in range(360)]


class BasicArrow:
    __slots__ = 'u', 'v', 'r', 'a', 'index_u', 'index_v', 'range_u', 'range_v', 'range_a'

    def __init__(self, u, v, r, a, r_u, r_v, r_a):
        self.u = u
        self.v = v
        self.a = a
        self.r = r
        self.index_u = self.u[0] * NB_POINTS * NB_POINTS + self.u[1] * NB_POINTS + self.u[2]
        self.index_v = self.v[0] * NB_POINTS * NB_POINTS + self.v[1] * NB_POINTS + self.v[2]
        self.range_u = r_u
        self.range_v = r_v
        self.range_a = r_a

    def raw_string(self):
        return str((self.u, self.v, self.r, self.a, self.range_u, self.range_v, self.range_a))

    @classmethod
    def parse(cls, raw_string):
        return cls(*literal_eval(raw_string))


class Arrow(BasicArrow):
    __slots__ = ()

    SMALLER = 0
    EQUALS = 1
    GREATER = 2

    def __init__(self, a: PixelGroup, b: PixelGroup):
        size_a = len(a.members)
        size_b = len(b.members)
        if round(size_a / size_b) > 1:
            rank = self.GREATER
        elif round(size_b / size_a) > 1:
            rank = self.SMALLER
        else:
            rank = self.EQUALS
        angle = round(functions.get_vector_angle(a.center, b.center)) % 360
        range_u = (
            SPACED_POINTS.near_indices_of[a.real_color[0]],
            SPACED_POINTS.near_indices_of[a.real_color[1]],
            SPACED_POINTS.near_indices_of[a.real_color[2]],
        )
        range_v = (
            SPACED_POINTS.near_indices_of[b.real_color[0]],
            SPACED_POINTS.near_indices_of[b.real_color[1]],
            SPACED_POINTS.near_indices_of[b.real_color[2]],
        )
        range_a = NEAR_INDICES_OF[angle]
        super().__init__(a.color, b.color, rank, INDEX_OF[angle], range_u, range_v, range_a)

    @property
    def key(self):
        return self.u, self.v, self.r, self.a

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return self.key == other.key

    def __lt__(self, other):
        return self.key < other.key

    def __str__(self):
        return f"{Color.rgb_to_hex(self.u)}-{self.r}-{self.a}{Color.rgb_to_hex(self.v)}"


def _sp_range(x):
    return range(max(0, x - 1), min(x + 2, NB_POINTS))


class _AbstractArrowClassifier:
    __slots__ = 'attribute', 'child_constructor', 'classifiers', 'value_to_index'

    @classmethod
    def builder(cls, *args, **kwargs):
        return lambda: cls(*args, **kwargs)

    def __init__(self, attribute, start, end, step, child_constructor):
        self.attribute = attribute
        self.child_constructor = child_constructor
        self.classifiers = []
        self.value_to_index = {}
        for index, value in enumerate(range(start, end, step)):
            self.classifiers.append(self.child_constructor())
            self.value_to_index[value] = index

    def add(self, arrow: BasicArrow, associated):
        self.classifiers[self.value_to_index[getattr(arrow, self.attribute)]].add(arrow, associated)

    def get_near_classifiers(self, arrow):
        # return self.classifiers[self.value_to_index[getattr(arrow, self.attribute)]],
        index = self.value_to_index[getattr(arrow, self.attribute)]
        if index:
            return self.classifiers[(index - 1):(index + 2)]
        return self.classifiers[:2]

    def near(self, arrow) -> List[Any]:
        return [classifier.near(arrow) for classifier in self.get_near_classifiers(arrow)]


class _SpacedIndicesClassifier(_AbstractArrowClassifier):
    __slots__ = 'real_attribute',

    def __init__(self, attribute, child_constructor):
        super().__init__(f'index_{attribute}', 0, NB_POINTS ** 3, 1, child_constructor)
        self.real_attribute = f'range_{attribute}'

    def get_near_classifiers(self, arrow):
        ranges = getattr(arrow, self.real_attribute)
        return [
            self.classifiers[i * NB_POINTS * NB_POINTS + j * NB_POINTS + k]
            for i in ranges[0]
            for j in ranges[1]
            for k in ranges[2]
        ]


class _ListArrowClassifier(_AbstractArrowClassifier):
    __slots__ = ()

    def __init__(self, attribute, start, end, step):
        super().__init__(attribute, start, end, step, list)

    def add(self, arrow: Arrow, associated):
        self.classifiers[self.value_to_index[getattr(arrow, self.attribute)]].append(associated)

    def near(self, arrow):
        return [classifier for classifier in self.get_near_classifiers(arrow)]


class _AngleClassifier(_ListArrowClassifier):
    __slots__ = 'real_attribute',

    def __init__(self, attribute):
        super().__init__(attribute, 0, 360, 45)
        self.real_attribute = f'range_{attribute}'

    def get_near_classifiers(self, arrow):
        return [self.classifiers[self.value_to_index[angle]] for angle in getattr(arrow, self.real_attribute)]


LENGTH = 256
NB_POINTS = 6
THRESHOLD = 0.5
MIN_COUNT = 10
SPACED_POINTS = SpacedPoints(length=LENGTH, nb_points=NB_POINTS)
SIMPLE_PIXEL_COMPARATOR = PixelComparator(SPACED_POINTS)
DISTANCE_PIXEL_COMPARATOR = DistancePixelComparator(0.0125, SPACED_POINTS)
PIXEL_COMPARATOR = DISTANCE_PIXEL_COMPARATOR


def generate_arrow_classifier():
    return _SpacedIndicesClassifier(
        'u', _SpacedIndicesClassifier.builder(
            'v', _AbstractArrowClassifier.builder(
                'r', 0, 3, 1, _AngleClassifier.builder(
                    'a'
                )
            )
        )
    )


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


def compute_arrows(raw_data: Iterable[Tuple[int, int, int]], width: int, height: int) -> List[Arrow]:
    groups = group_pixels(raw_data, width, height)
    edges = []
    # Order groups in grid.
    rows = {}  # type: Dict[float, Dict[float, List[PixelGroup]]]
    for g in groups:
        # Keep only groups with at least 3 members.
        if len(g.members) > 2:
            x, y = g.center
            rows.setdefault(y, {}).setdefault(x, []).append(g)
    # Collect arrows following groups in grid (then biggest groups first),
    # and only from a group to another (not in both directions).
    for y, row in sorted(rows.items()):
        for x, col in sorted(row.items()):
            for e in sorted(col, key=lambda gr: len(gr.members)):  # type: PixelGroup
                for other in e.connections:
                    other.connections.remove(e)
                    edges.append(Arrow(e, other))
    return edges


def async_compute_arrows(context):
    i, m, t, n = context
    if (i + 1) % 500 == 0:
        n.notify(notifications.VideoJob('', i + 1, t))
    return m.identifier, compute_arrows(m.data(), m.width, m.height)


def flatten(data: list):
    while isinstance(data[0], list):
        data = [el for seq in data for el in seq]
    return data


def _reduce(indices, index_to_position):
    output = ['0'] * len(index_to_position)
    for index in indices:
        output[index_to_position[index]] = '1'
    return ''.join(output)


def categorize_arrows(output: List[Tuple[str, List[Arrow]]], videos: Dict[str, Video]):
    path_to_arrows = {}
    arrow_to_paths = {}

    with Profiler('Path to arrows and arrow classifier.'):
        for path, arrows in output:
            if arrows:
                video_id = videos[path].video_id
                path_to_arrows[video_id] = [arrow.raw_string() for arrow in arrows]
                for arrow in arrows:
                    arrow_to_paths.setdefault(arrow.raw_string(), []).append(video_id)

    return path_to_arrows, arrow_to_paths


def job_find_similarities(job):
    tasks, job_id, threshold, min_count, workspace, notifier = job
    job_count = len(tasks)
    DEFAULT_NOTIFIER.notify(notifications.Message(f'[{job_id}] Loading workspace.'))
    arrow_to_paths = Workspace.load(workspace)
    arrow_classifier = generate_arrow_classifier()
    for arrow_raw_string, paths in arrow_to_paths.items():
        arrow_classifier.add(BasicArrow.parse(arrow_raw_string), paths)
    DEFAULT_NOTIFIER.notify(notifications.Message(f'[{job_id}] Loaded workspace.'))
    similarities = {}
    for i, (path, arrows) in enumerate(tasks):
        connected_paths = {}
        for arrow_raw_string in arrows:
            for other_path in flatten(arrow_classifier.near(BasicArrow.parse(arrow_raw_string))):
                connected_paths[other_path] = connected_paths.get(other_path, 0) + 1
        del connected_paths[path]
        for other_path in similarities.get(path, ()):
            del connected_paths[other_path]
        if connected_paths:
            connections = iter(connected_paths.items())
            p, c = next(connections)
            highest_paths = [p]
            highest_count = c
            for other_path, arrow_count in connections:
                if highest_count < arrow_count:
                    highest_paths = [other_path]
                    highest_count = arrow_count
                elif highest_count == arrow_count:
                    highest_paths.append(other_path)
            if highest_paths and highest_count >= min_count and highest_count >= (len(arrows) * threshold):
                for other_path in highest_paths:
                    similarities.setdefault(other_path, {})[path] = highest_count / len(arrows)
        if (i + 1) % 2 == 0:
            notifier.notify(notifications.VideoJob(job_id, i + 1, job_count))
    notifier.notify(notifications.VideoJob(job_id, job_count, job_count))
    return similarities


def main():
    cpu_count = max(1, os.cpu_count() - 2)
    api = API(TEST_LIST_FILE_PATH, update=False)
    videos = list(api.database.readable.found.with_thumbnails)  # type: List[Video]
    videos_dict = {v.filename.path: v for v in videos}  # type: Dict[str, Video]
    min_dict = {m.identifier: m for m in api.database.ensure_miniatures(return_miniatures=True)}
    miniatures = [min_dict[video.filename.path] for video in videos]
    tasks = [(i, m, len(miniatures), DEFAULT_NOTIFIER) for i, m in enumerate(miniatures)]

    with Profiler(f'Segment {len(tasks)} videos.'):
        with Pool(cpu_count) as p:
            output = list(p.imap(async_compute_arrows, tasks))
    DEFAULT_NOTIFIER.notify(notifications.VideoJob('', len(miniatures), len(miniatures)))
    assert len(output) == len(tasks), (len(output), len(tasks))

    special_property = '__image__'
    DEFAULT_NOTIFIER.notify(notifications.Message('Create video property', special_property))
    if not api.database.has_prop_type(special_property):
        api.database.add_prop_type(PropType(special_property, '', True))

    DEFAULT_NOTIFIER.notify(notifications.Message('Clear video property', special_property))
    for video in videos:
        video.properties[special_property] = []

    with Profiler('Create video graph.'):
        pta, atp = categorize_arrows(output, videos_dict)
        DEFAULT_NOTIFIER.notify(notifications.Message(len(atp), 'unique arrow(s).'))

    ####################################################################################################################
    with Profiler('Create workspace.'):
        workspace = Workspace.save(atp)
        DEFAULT_NOTIFIER.notify(notifications.Message(workspace))

    with Profiler('Async find similarities'):
        t = list(pta.items())
        j = functions.dispatch_tasks(t, cpu_count, [THRESHOLD, MIN_COUNT, workspace, DEFAULT_NOTIFIER])
        results = functions.parallelize(job_find_similarities, j, cpu_count)

    i = 0
    for similarities in results:
        for video_id, video_indices in similarities.items():
            for other_id, similarity in video_indices.items():
                tag = f"{i}-{round(similarity * 100) / 100}"
                DEFAULT_NOTIFIER.notify(
                    notifications.Message(f'[{i + 1}] Similarity({len(video_indices) + 1}) tag({tag})'))
                api.database.get_video_from_id(video_id).properties[special_property].append(tag)
                api.database.get_video_from_id(other_id).properties[special_property].append(tag)
                i += 1
    ####################################################################################################################

    for video in videos:
        video.properties[special_property].sort()
    api.database.save()


class Tests:

    @classmethod
    def segment(cls, data, width, height):
        groups = group_pixels(data, width, height)
        print(len(groups), 'groups')
        output = [(0, 0, 0) for _ in range(width * height)]
        for group in groups:
            for index in group.members:
                output[index] = group.color
        return output

    @classmethod
    def _average_distance(cls, values):
        if len(values) < 2:
            return 0
        total_distances = 0
        for i in range(1, len(values)):
            total_distances += abs(values[i] - values[i - 1])
        return total_distances / (len(values) - 1)

    @classmethod
    def contrast_rate(cls, data):
        grays = {int(sum(p) / 3) for p in data}
        values = sorted(grays)
        if len(values) < 2:
            return 0
        best_distance = 255 / (len(values) - 1)
        average_distance = cls._average_distance(values)
        return average_distance / best_distance

    @classmethod
    def main(cls):
        from pysaurus.core.modules import ImageUtils, Display
        api = API(TEST_LIST_FILE_PATH, update=False)
        p1 = r"R:\donnees\autres\p\Harley Dean - bkb16182-1080p.mp4"
        p2 = r"F:\donnees\autres\p\Real butler should be able to serve dinner and fuck his masters.mp4"
        # p1 = r"H:\donnees\autres\p\Watch Caribbeancom 092019-001 Haruka Juri Masochist Nipple Online  JAV HD FREE ONLINE 1080p.mp4"
        # p2 = r"G:\donnees\autres\p\Rebecca More - Big Boobs In Army.mp4"
        v1 = api.database.get_video_from_filename(p1)
        v2 = api.database.get_video_from_filename(p2)
        i1 = ImageUtils.open_rgb_image(v1.thumbnail_path.path)
        i2 = ImageUtils.open_rgb_image(v2.thumbnail_path.path)
        c1 = cls.segment(i1.getdata(), *i1.size)
        c2 = cls.segment(i2.getdata(), *i2.size)
        print(cls.contrast_rate(i1.getdata()), cls.contrast_rate(i2.getdata()))
        o1 = equalize(i1.getdata())
        o2 = equalize(i2.getdata())
        d1 = cls.segment(o1, *i1.size)
        d2 = cls.segment(o2, *i2.size)
        Display.from_images(
            i1, i2,
            ImageUtils.new_rgb_image(c1, *i1.size), ImageUtils.new_rgb_image(c2, *i2.size),
            # ImageUtils.new_rgb_image(o1, *i1.size), ImageUtils.new_rgb_image(o2, *i2.size),
            # ImageUtils.new_rgb_image(d1, *i1.size), ImageUtils.new_rgb_image(d2, *i2.size),
        )


if __name__ == '__main__':
    # Tests.main()
    with Profiler('MAIN'):
        main()
