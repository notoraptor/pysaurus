import math
import os
from abc import abstractmethod
from multiprocessing import Pool
from typing import List, Tuple, Dict, Set, Any, Union

from pysaurus.core import functions
from pysaurus.core.database import notifications
from pysaurus.core.database.api import API
from pysaurus.core.database.properties import PropType
from pysaurus.core.database.video import Video
from pysaurus.core.notification import DEFAULT_NOTIFIER
from pysaurus.core.profiling import Profiler
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH
from pysaurus.tests.trash import SpacedPoints


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
    __slots__ = 'threshold', 'limit'

    def __init__(self, similarity_percent: Union[int, float]):
        self.threshold = (100 - similarity_percent) / 100
        self.limit = self.threshold * 255 * math.sqrt(3)

    def normalize_data(self, data, width):
        return list(data)

    def pixels_are_close(self, data, i, j, width):
        r1, g1, b1 = data[i]
        r2, g2, b2 = data[j]
        distance = math.sqrt((r1 - r2) * (r1 - r2) + (g1 - g2) * (g1 - g2) + (b1 - b2) * (b1 - b2))
        return distance <= self.limit

    def common_color(self, data, indices, width):
        nb_indices = len(indices)
        sum_r = 0
        sum_g = 0
        sum_b = 0
        for index in indices:
            r, g, b = data[index]
            sum_r += r
            sum_g += g
            sum_b += b
        return sum_r / nb_indices, sum_g / nb_indices, sum_b / nb_indices


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

    def __init__(self, color: Tuple, center: Tuple, size: int):
        color = tuple(SPACED_COLOR.nearest_point(value) for value in color)
        # Positions are in interval [0; 32]. We want to put it on interval [0; 64] for a better resolution.
        # So, we multiply position value by 2.
        center = tuple(SPACED_POSITION.nearest_point(2 * value) for value in center)
        size = SPACED_SIZE.nearest_point(size)
        self.color = color
        self.center = center
        self.size = size

    key = property(lambda self: (self.color, self.center, self.size))

    def __str__(self):
        return str(self.key)

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return self.key == other.key

    def __lt__(self, other):
        return self.key < other.key


class PixelGroup:
    __slots__ = 'color', 'image_width', 'identifier', 'members'

    def __init__(self, color: Tuple[float, float, float], image_width: int, identifier: int, members: Set[int]):
        self.color = color
        self.image_width = image_width
        self.identifier = identifier
        self.members = members

    def __str__(self):
        return (
            f"PixelGroup({self.identifier + 1} "
            f"{self.color}, "
            f"{len(self.members)} member{functions.get_plural_suffix(len(self.members))}, "
            f"center {self.center})"
        )

    def __hash__(self):
        return hash(self.identifier)

    def __eq__(self, other):
        return self.identifier == other.identifier

    def to_basic_group(self):
        return BasicGroup(tuple(round(v) for v in self.color), tuple(round(v) for v in self.center), len(self.members))

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


GROUP_MIN_SIZE = 4
CPU_COUNT = max(1, os.cpu_count() - 2)
THRESHOLD = 0.5
MIN_COUNT = 5
PIXEL_COMPARATOR = DistancePixelComparator(98.75)
SPACED_COLOR = SpacedPoints(256, 4)
SPACED_POSITION = SpacedPoints(64, 8)
SPACED_SIZE = SpacedPoints(1024, 32)


def group_pixels(raw_data, width, height) -> List[PixelGroup]:
    data = PIXEL_COMPARATOR.normalize_data(raw_data, width)
    graph = Graph()
    # Connect pixels in first line.
    for current_index in range(1, width):
        previous_index = current_index - 1
        if PIXEL_COMPARATOR.pixels_are_close(data, current_index, previous_index, width):
            graph.connect(current_index, previous_index)
    # Connect pixels in next lines.
    for y in range(1, height):
        # Connect first pixel.
        current_index = y * width
        above_index = current_index - width
        if PIXEL_COMPARATOR.pixels_are_close(data, current_index, above_index, width):
            graph.connect(current_index, above_index)
        # Connect next pixels.
        for x in range(1, width):
            current_index = y * width + x
            above_index = current_index - width
            previous_index = current_index - 1
            top_left_index = current_index - width - 1
            if PIXEL_COMPARATOR.pixels_are_close(data, current_index, above_index, width):
                graph.connect(current_index, above_index)
            if PIXEL_COMPARATOR.pixels_are_close(data, current_index, previous_index, width):
                graph.connect(current_index, previous_index)
            if PIXEL_COMPARATOR.pixels_are_close(data, current_index, top_left_index, width):
                graph.connect(current_index, top_left_index)
    # Get groups and connect each pixel to its group.
    groups = []  # type: List[PixelGroup]
    while graph.edges:
        index, other_indices = graph.edges.popitem()
        group_id = len(groups)
        group = {index}
        while other_indices:
            other_index = other_indices.pop()
            if other_index not in group:
                group.add(other_index)
                other_indices.update(graph.edges.pop(other_index))
        groups.append(PixelGroup(PIXEL_COMPARATOR.common_color(data, group, width), width, group_id, group))
    return groups


def compute_groups(miniature) -> List[BasicGroup]:
    return [group.to_basic_group()
            for group in group_pixels(miniature.data(), miniature.width, miniature.height)
            if len(group.members) >= GROUP_MIN_SIZE]


def async_compute_groups(context):
    index_task, miniature, nb_all_tasks, notifier = context
    if (index_task + 1) % 1000 == 0:
        notifier.notify(notifications.VideoJob('', index_task + 1, nb_all_tasks))
    return miniature.identifier, compute_groups(miniature)


def job_find_similarities(job):
    tasks, job_id, threshold, min_count, gid_to_vid_s, notifier = job
    job_count = len(tasks)
    similarities = {}
    for i, (vid, gid_s) in enumerate(tasks):
        connected_vid_s = {}
        for gid in gid_s:
            out_vid_s = set()
            for out_vid in gid_to_vid_s[gid]:
                # If a groupm (surprisingly) appears many times in a same video, we count it only once.
                if out_vid not in out_vid_s:
                    connected_vid_s[out_vid] = connected_vid_s.get(out_vid, 0) + 1
                    out_vid_s.add(out_vid)
        del connected_vid_s[vid]
        for other_vid in similarities.get(vid, ()):
            del connected_vid_s[other_vid]
        if connected_vid_s:
            connections = iter(connected_vid_s.items())
            v, highest_count = next(connections)
            highest_vid_s = [v]
            for other_v, other_c in connections:
                if highest_count < other_c:
                    highest_vid_s = [other_v]
                    highest_count = other_c
                elif highest_count == other_c:
                    highest_vid_s.append(other_v)
            if highest_count >= min_count and highest_count >= threshold * len(gid_s):
                for other_v in highest_vid_s:
                    similarities.setdefault(other_v, {})[vid] = (highest_count, len(gid_s))
        if (i + 1) % 500 == 0:
            notifier.notify(notifications.VideoJob(job_id, i + 1, job_count))
    notifier.notify(notifications.VideoJob(job_id, job_count, job_count))
    return similarities


def main():
    api = API(TEST_LIST_FILE_PATH, update=False)
    videos = list(api.database.readable.found.with_thumbnails) + list(
        api.database.readable.not_found.with_thumbnails)  # type: List[Video]
    videos_dict = {v.filename.path: v for v in videos}  # type: Dict[str, Video]
    vid_to_v = {v.video_id: v for v in videos}  # type: Dict[int, Video]
    min_dict = {m.identifier: m for m in api.database.ensure_miniatures(return_miniatures=True)}
    miniatures = [min_dict[video.filename.path] for video in videos]

    tasks = [(i, m, len(miniatures), DEFAULT_NOTIFIER) for i, m in enumerate(miniatures)]
    with Profiler(f'Segment {len(tasks)} videos.'):
        with Pool(CPU_COUNT) as p:
            output = list(p.imap(async_compute_groups, tasks))
    DEFAULT_NOTIFIER.notify(notifications.VideoJob('', len(miniatures), len(miniatures)))

    it_output = iter(output)
    p, ig = next(it_output)
    ig = set(ig)
    all_groups = set(ig)
    min_g = max_g = len(ig)
    video_to_groups = {p: list(ig)}
    group_to_videos = {g: [p] for g in ig}
    for path, image_groups in it_output:
        len_before = len(image_groups)
        image_groups = set(image_groups)
        if len(image_groups) != len_before:
            print(f"Nb. groups from {len_before} to {len(image_groups)} for: {path}")
        all_groups.update(image_groups)
        min_g = min(min_g, len(image_groups))
        max_g = max(max_g, len(image_groups))
        video_to_groups[path] = list(image_groups)
        for g in image_groups:
            group_to_videos.setdefault(g, []).append(path)

    all_groups = list(all_groups)
    assert len(video_to_groups) == len(videos)
    assert len(group_to_videos) == len(all_groups)
    print('Total groups', len(all_groups))
    print('Min group size', min_g)
    print('Max group size', max_g)
    print('Average group size', len(all_groups) / len(output))
    for path, groups in video_to_groups.items():
        if len(groups) == min_g:
            print('Min', path)
        if len(groups) == max_g:
            print('Max', path)

    with Profiler('Compress data'):
        group_to_gid = {g: i for i, g in enumerate(all_groups)}
        vid_to_gid_s = {videos_dict[path].video_id: [group_to_gid[g] for g in groups]
                        for path, groups in video_to_groups.items()}
        gid_to_vid_s = {group_to_gid[g]: [videos_dict[p].video_id for p in ps] for g, ps in group_to_videos.items()}

    tasks = list(vid_to_gid_s.items())
    jobs = functions.dispatch_tasks(tasks, CPU_COUNT, [THRESHOLD, MIN_COUNT, gid_to_vid_s, DEFAULT_NOTIFIER])
    with Profiler('Async find similarities'):
        results = functions.parallelize(job_find_similarities, jobs, CPU_COUNT)

    special_property = '__image__'
    DEFAULT_NOTIFIER.notify(notifications.Message('Create video property', special_property))
    if not api.database.has_prop_type(special_property):
        api.database.add_prop_type(PropType(special_property, '', True))
    DEFAULT_NOTIFIER.notify(notifications.Message('Clear video property', special_property))
    for video in videos:
        video.properties[special_property] = []

    sim_groups = []
    sim_graph = Graph()
    weights = {}
    for similarities in results:
        for video_id, video_indices in similarities.items():
            for other_id, (a, b) in video_indices.items():
                sim_graph.connect(video_id, other_id)
                weights[(video_id, other_id)] = (a, b)
    while sim_graph.edges:
        v, vs = sim_graph.edges.popitem()
        g = {v}
        while vs:
            ov = vs.pop()
            if ov not in g:
                g.add(ov)
                vs.update(sim_graph.edges.pop(ov))
        sim_groups.append(list(g))
    s = int(1 + math.log10(len(sim_groups)))
    sim_vids = set()
    for tag_id, similar_video_indices in enumerate(sim_groups):
        sir = []
        for i in range(len(similar_video_indices)):
            for j in range(i + 1, len(similar_video_indices)):
                p1 = similar_video_indices[i], similar_video_indices[j]
                p2 = similar_video_indices[j], similar_video_indices[i]
                for p in (p1, p2):
                    if p in weights:
                        a, b = weights[p]
                        similarity = round(a * 100 / b) / 100
                        sir.append((similarity, a, b))
        sir = sorted(set(sir))
        tag = f'{str(tag_id + 1).rjust(s, "0")} {" ".join(f"{s}({a}/{b})" for s, a, b in sir)}'
        sim_vids.update(similar_video_indices)
        for video_id in similar_video_indices:
            vid_to_v[video_id].properties[special_property].extend([tag, '(similar)'])
    assert len(sim_vids) == sum(len(sg) for sg in sim_groups), (len(sim_vids), sum(len(sg) for sg in sim_groups))
    DEFAULT_NOTIFIER.notify(notifications.Message(f'Similar groups: {len(sim_groups)}, similar videos: {len(sim_vids)}'))
    for video in videos:
        video.properties[special_property] = sorted(set(video.properties[special_property]))
    api.database.save()


if __name__ == '__main__':
    with Profiler('Main function.'):
        main()
