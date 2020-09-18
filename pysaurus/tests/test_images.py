import os
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

_MAP_POINTS = {}


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


class SpacedPoints:
    """
    for interval length = 256:
    k = 2;  c = 8;      l = 254
    k = 4;  c = 64;     l = 84
    k = 6;  c = 216;    l = 50
    k = 16; c = 4096;   l = 16
    k = 18; c = 5832;   l = 14
    k = 52; c = 140608; l = 4
    k = 86; c = 636056; l = 2
    """

    __slots__ = 'd',

    def __init__(self, length=256, nb_points=6):
        if length not in _MAP_POINTS:
            _MAP_POINTS[length] = _available_points_and_spaces(length)
        points = _MAP_POINTS[length]
        assert nb_points in points, tuple(points)
        self.d = points[nb_points] + 1

    def nearest_point(self, value: int):
        # 0 <= value < interval length
        i = value // self.d
        before = i * self.d
        after = (i + 1) * self.d
        if value - before < after - value:
            return before
        return after

    def nearest_points(self, values: Union[List[int], Tuple[int, int, int]]):
        return type(values)(self.nearest_point(value) for value in values)


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
    __slots__ = 'color', 'image_width', 'identifier', 'members', 'connections'

    def __init__(self, color: Tuple[int, int, int], image_width: int, identifier: int, members: Set[int]):
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


class Arrow:
    __slots__ = 'u', 'v', 'r', 'a'

    SMALLER = 0
    EQUALS = 1
    GREATER = 2

    @classmethod
    def categorize_angle(cls, degrees):
        """Return nearest multiple of 45 degrees to given degrees."""
        index_before = int(degrees // 45)
        angle_before = index_before * 45
        angle_after = (index_before + 1) * 45
        if (degrees - angle_before) < (angle_after - degrees):
            return angle_before
        return angle_after % 360

    def __init__(self, a: PixelGroup, b: PixelGroup):
        size_a = len(a.members)
        size_b = len(b.members)
        if size_a // size_b > 1:
            rank = self.GREATER
        elif size_b // size_a > 1:
            rank = self.SMALLER
        else:
            rank = self.EQUALS
        self.u = a.color
        self.v = b.color
        self.r = rank
        self.a = self.categorize_angle(functions.get_vector_angle(a.center, b.center))

    @property
    def key(self):
        return self.u + self.v + (self.r, self.a)

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return self.key == other.key

    def __str__(self):
        return f"{Color.rgb_to_hex(self.u)}-{self.r}-{self.a}{Color.rgb_to_hex(self.v)}"


SPACED_POINTS = SpacedPoints()


def segment_image(raw_data: Iterable[Tuple[int, int, int]], width: int, height: int) -> List[Arrow]:
    """Column to right, row to bottom"""
    data = [SPACED_POINTS.nearest_points(pixel) for pixel in raw_data]
    graph = Graph()
    disconnected = Graph()
    # Connect pixels in first line.
    for current_index in range(1, width):
        previous_index = current_index - 1
        if data[previous_index] == data[current_index]:
            graph.connect(current_index, previous_index)
        else:
            disconnected.connect(current_index, previous_index)
    # Connect pixels in next lines.
    for y in range(1, height):
        # Connect first pixel.
        current_index = y * width
        above_index = current_index - width
        if data[current_index] == data[above_index]:
            graph.connect(current_index, above_index)
        else:
            disconnected.connect(current_index, above_index)
        # Connect next pixels.
        for x in range(1, width):
            current_index = y * width + x
            above_index = current_index - width
            previous_index = current_index - 1
            if data[current_index] == data[above_index]:
                graph.connect(current_index, above_index)
            else:
                disconnected.connect(current_index, above_index)
            if data[current_index] == data[previous_index]:
                graph.connect(current_index, previous_index)
            else:
                disconnected.connect(current_index, previous_index)
    # Get groups and connect each pixel to its group.
    groups = []  # type: List[PixelGroup]
    _ungrouped_indices = set(range(width * height))  # type: Set[int]
    _index_to_group = {}  # type: Dict[int, int]
    while graph.edges:
        group_id = len(groups)
        index, other_indices = graph.edges.popitem()
        color = data[index]
        group = {index}
        _index_to_group[index] = group_id
        _ungrouped_indices.remove(index)
        while other_indices:
            other_index = other_indices.pop()
            if other_index not in group:
                group.add(other_index)
                _index_to_group[other_index] = group_id
                _ungrouped_indices.remove(other_index)
                other_indices.update(graph.edges.pop(other_index))
        groups.append(PixelGroup(color, width, group_id, group))
    for ungrouped_index in _ungrouped_indices:
        disconnected.remove(ungrouped_index)
    # Connect groups.
    for in_index, out_indices in disconnected.edges.items():
        id_group_in = _index_to_group[in_index]
        for out_index in out_indices:
            groups[id_group_in].connections.add(groups[_index_to_group[out_index]])
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


def async_segment_image(context):
    i, m, t, n = context
    if (i + 1) % 500 == 0:
        n.notify(notifications.VideoJob('', i + 1, t))
    return m.identifier, segment_image(m.data(), m.width, m.height)


def job_find_similarities(job):
    tasks, job_id, threshold, min_count, workspace, notifier = job
    job_count = len(tasks)
    arrow_to_paths = Workspace.load(workspace)
    similarities = {}
    for i, (path, arrows) in enumerate(tasks):
        connected_paths = {}
        for arrow in arrows:
            for other_path in arrow_to_paths[arrow]:
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
        if (i + 1) % 100 == 0:
            notifier.notify(notifications.VideoJob(job_id, i + 1, job_count))
    notifier.notify(notifications.VideoJob(job_id, job_count, job_count))
    return similarities


def main():
    cpu_count = max(1, os.cpu_count() - 1)
    api = API(TEST_LIST_FILE_PATH, update=False)
    videos = list(api.database.readable.found.with_thumbnails)  # type: List[Video]
    videos_dict = {v.filename.path: v for v in videos}  # type: Dict[str, Video]
    min_dict = {m.identifier: m for m in api.database.ensure_miniatures(return_miniatures=True)}
    miniatures = [min_dict[video.filename.path] for video in videos]
    tasks = [(i, m, len(miniatures), DEFAULT_NOTIFIER) for i, m in enumerate(miniatures)]

    with Profiler(f'Segment {len(tasks)} videos.'):
        with Pool(cpu_count) as p:
            output = list(p.imap(async_segment_image, tasks))
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
        pta = {}
        atp = {}
        for _path, _arrows in output:
            if _arrows:
                vid = videos_dict[_path].video_id
                ars = set(str(a) for a in _arrows)
                pta[vid] = ars
                for a in ars:
                    atp.setdefault(a, []).append(vid)

    threshold = 0.5
    min_count = 10

    ####################################################################################################################
    workspace = Workspace.save(atp)
    t = list(pta.items())
    j = functions.dispatch_tasks(t, cpu_count, [threshold, min_count, workspace, DEFAULT_NOTIFIER])
    with Profiler('Async find similarities'):
        results = functions.parallelize(job_find_similarities, j, cpu_count)

    i = 0
    for similarities in results:
        for video_id, video_indices in similarities.items():
            for other_id, similarity in video_indices.items():
                tag = f"{i}-{round(similarity * 100) / 100}"
                DEFAULT_NOTIFIER.notify(notifications.Message(f'[{i + 1}] Similarity({len(video_indices) + 1}) tag({tag})'))
                api.database.get_video_from_id(video_id).properties[special_property].append(tag)
                api.database.get_video_from_id(other_id).properties[special_property].append(tag)
                i += 1
    ####################################################################################################################

    for video in videos:
        video.properties[special_property].sort()
    api.database.save()


if __name__ == '__main__':
    with Profiler('MAIN'):
        main()
