import itertools
import math
import os
from abc import abstractmethod
from multiprocessing import Pool
from typing import List, Tuple, Dict, Set, Any, Union, Optional

import ujson as json

from pysaurus.core import functions
from pysaurus.core.components import AbsolutePath
from pysaurus.core.database import notifications
from pysaurus.core.database.api import API
from pysaurus.core.database.properties import PropType
from pysaurus.core.database.video import Video
from pysaurus.core.native.video_raptor.miniature import Miniature
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


def _categorize_position(x, y, width, step):
    return int(y // step) * (width // step) + int(x // step)


def _categorize_value(x, step):
    return int(x // step)


def _categorize_sub_position(x, y, width, step):
    p_x = _categorize_sub_value(x, step)
    p_y = _categorize_sub_value(y, step)
    return p_y * (1 + width // step) + p_x


def _categorize_sub_value(x, step):
    return int((int(x // (step // 2)) + 1) // 2)


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

    def to_basic_group(self, spaced_color: SpacedPoints, spaced_position: SpacedPoints, spaced_size: SpacedPoints):
        color = tuple(spaced_color.nearest_point(value) for value in self.color)
        center = tuple(spaced_position.nearest_point(value) for value in self.center)
        size = spaced_size.nearest_point(len(self.members))
        return BasicGroup(color, center, size)

    def to_basic_group_raw(self):
        return BasicGroup(self.color, self.center, len(self.members))

    def to_basic_group_intervals(self, nb_color_points, nb_position_points, nb_size_points):
        color = tuple(_categorize_value(value, 256 // nb_color_points) for value in self.color)
        center = _categorize_position(*self.center, 32, 32 // nb_position_points)
        size = _categorize_value(len(self.members), 1024 // nb_size_points)
        return BasicGroup(color, center, size)

    def to_basic_group_sub_intervals(self, nb_color_points, nb_position_points, nb_size_points):
        color = tuple(_categorize_sub_value(value, 256 // nb_color_points) for value in self.color)
        center = _categorize_sub_position(*self.center, 32, 32 // nb_position_points)
        size = _categorize_sub_value(len(self.members), 1024 // nb_size_points)
        return BasicGroup(color, center, size)

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


class GroupComputer:
    __slots__ = 'group_min_size', 'pixel_comparator'

    def __init__(self, *, group_min_size, similarity_percent):
        self.group_min_size = group_min_size
        self.pixel_comparator = DistancePixelComparator(similarity_percent)

    def group_pixels(self, raw_data, width, height) -> List[PixelGroup]:
        data = self.pixel_comparator.normalize_data(raw_data, width)
        graph = Graph()
        # Connect pixels in first line.
        for current_index in range(1, width):
            previous_index = current_index - 1
            if self.pixel_comparator.pixels_are_close(data, current_index, previous_index, width):
                graph.connect(current_index, previous_index)
        # Connect pixels in next lines.
        for y in range(1, height):
            # Connect first pixel.
            current_index = y * width
            above_index = current_index - width
            if self.pixel_comparator.pixels_are_close(data, current_index, above_index, width):
                graph.connect(current_index, above_index)
            # Connect next pixels.
            for x in range(1, width):
                current_index = y * width + x
                above_index = current_index - width
                previous_index = current_index - 1
                top_left_index = current_index - width - 1
                if self.pixel_comparator.pixels_are_close(data, current_index, above_index, width):
                    graph.connect(current_index, above_index)
                if self.pixel_comparator.pixels_are_close(data, current_index, previous_index, width):
                    graph.connect(current_index, previous_index)
                if self.pixel_comparator.pixels_are_close(data, current_index, top_left_index, width):
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
            groups.append(PixelGroup(self.pixel_comparator.common_color(data, group, width), width, group_id, group))
        return groups

    def compute_groups(self, miniature) -> List[PixelGroup]:
        # compute_groups
        return [group
                for group in self.group_pixels(miniature.data(), miniature.width, miniature.height)
                if len(group.members) >= self.group_min_size]

    def async_compute(self, context):
        index_task, miniature, nb_all_tasks, notifier = context
        if (index_task + 1) % PRINT_STEP == 0:
            notifier.notify(notifications.VideoJob('', index_task + 1, nb_all_tasks))
        return miniature.identifier, self.compute_groups(miniature)


class SpacedPoints32To64(SpacedPoints):
    # Positions are in interval [0; 32]. We want to put it on interval [0; 64] for a better resolution.
    # So, we multiply position value by 2.

    def __init__(self, nb_points):
        super().__init__(64, nb_points)

    def nearest_point(self, value: Union[int, float]):
        return super().nearest_point(2 * value)


def job_find_similarities_(job):
    tasks, job_id, threshold, min_count, vid_to_len, gid_to_vid_s, vid_to_b_to_s, notifier = job
    job_count = len(tasks)
    similarities = {}
    for i, (vid, gid_s) in enumerate(tasks):
        connected_vid_s = {}
        for gid in gid_s:
            for out_vid in gid_to_vid_s[gid]:
                connected_vid_s[out_vid] = connected_vid_s.get(out_vid, 0) + 1
        del connected_vid_s[vid]
        for other_v, other_c in connected_vid_s.items():
            if other_c >= threshold * len(gid_s):
                similarities.setdefault(other_v, {})[vid] = (other_c, len(gid_s))
        if (i + 1) % PRINT_STEP == 0:
            notifier.notify(notifications.VideoJob(job_id, i + 1, job_count))
    notifier.notify(notifications.VideoJob(job_id, job_count, job_count))
    return similarities


def job_find_similarities(job):
    tasks, job_id, threshold, min_count, vid_to_len, gid_to_vid_s, vid_to_b_to_s, notifier = job
    job_count = len(tasks)
    similarities = {}
    for i, (vid, gid_s) in enumerate(tasks):
        connected_vid_s = {}
        for gid in gid_s:
            for out_vid in gid_to_vid_s[gid]:
                connected_vid_s.setdefault(out_vid, []).append(gid)
                # connected_vid_s[out_vid] = connected_vid_s.get(out_vid, 0) + 1
        del connected_vid_s[vid]
        for other_v, other_g in connected_vid_s.items():
            cs = sum(vid_to_b_to_s[vid][g] for g in other_g)
            ts = sum(vid_to_b_to_s[vid].values())
            if cs >= threshold * ts:
                similarities.setdefault(other_v, {})[vid] = (len(other_g), len(gid_s))
            # if len(other_g) >= threshold * len(gid_s):
            #     similarities.setdefault(other_v, {})[vid] = (len(other_g), len(gid_s))
        if (i + 1) % PRINT_STEP == 0:
            notifier.notify(notifications.VideoJob(job_id, i + 1, job_count))
    notifier.notify(notifications.VideoJob(job_id, job_count, job_count))
    return similarities


def run(
        api: API,
        videos: List[Video],
        videos_dict: Dict[str, Video],
        vid_to_v: Dict[int, Video],
        miniatures: List[Miniature],
        threshold=0.5,
        min_count=5,
        nb_color_points=6,
        nb_position_points=8,
        nb_size_points=32,
        group_min_size=4,
        pixel_distance_radius=2,
        debug=True,
        display_extremums=False,
        duration_diff_seconds=None,
        group_classifier=None,
        just_display_groups=False,
        return_groups=False,
        watch=None
):
    if group_classifier is None:
        group_classifier = ('default',)
    elif isinstance(group_classifier, str):
        group_classifier = (group_classifier,)
    else:
        assert isinstance(group_classifier, (list, tuple, set)), f'Group classifier must be an optional (sequence of) string, got {group_classifier}'

    similarity_percent = ((255 - pixel_distance_radius) * 100 / 255)

    cpu_count = max(1, os.cpu_count() - 2)
    group_computer = GroupComputer(
        group_min_size=group_min_size,
        similarity_percent=similarity_percent
    )

    tasks = [(i, m, len(miniatures), DEFAULT_NOTIFIER) for i, m in enumerate(miniatures)]
    with Profiler(f'Segment {len(tasks)} videos.'):
        with Pool(cpu_count) as p:
            raw_output = list(p.imap(group_computer.async_compute, tasks))
    DEFAULT_NOTIFIER.notify(notifications.VideoJob('', len(miniatures), len(miniatures)))

    results = []

    for classifier in group_classifier:
        print('Classifier', classifier)

        if classifier == 'default':
            spaced_color = SpacedPoints(256, nb_color_points)
            spaced_position = SpacedPoints32To64(nb_position_points)
            spaced_size = SpacedPoints(1024, nb_size_points)
            callback = lambda g: g.to_basic_group(spaced_color, spaced_position, spaced_size)
        elif classifier == 'intervals':
            callback = lambda g: g.to_basic_group_intervals(nb_color_points, nb_position_points, nb_size_points)
        elif classifier == 'sub_intervals':
            callback = lambda g: g.to_basic_group_sub_intervals(nb_color_points, nb_position_points, nb_size_points)
        elif classifier == 'raw':
            callback = lambda g: g.to_basic_group_raw()
        else:
            raise ValueError(f'Unknown group classifier option: {classifier}')

        output = []
        vid_to_b_to_s = {}
        for p, gs in raw_output:
            b_to_s = {}
            bs = []
            for g in gs:
                b = callback(g)
                b_to_s[b] = b_to_s.get(b, 0) + len(g.members)
                bs.append(b)
            vid_to_b_to_s[videos_dict[p].video_id] = b_to_s
            output.append((p, bs))

        if just_display_groups:
            tmp = {}
            for p, gs in output:
                tmp[p] = set(gs)
            ps = sorted(tmp)
            print('Nb. Groups:')
            for p in ps:
                print(f'\t{len(tmp[p])}\t{p}')
            print('Common groups:')
            for i in range(len(ps)):
                for j in range(i + 1, len(ps)):
                    common = tmp[ps[i]] & tmp[ps[j]]
                    print(f'\t{len(tmp[ps[i]])}\t{ps[i]}')
                    print(f'\t{len(tmp[ps[j]])}\t{ps[j]}')
                    print(f'\t\t{len(common)}')
            return

        if watch:
            to_watch = [(p, gs) for (p, gs) in output if p in watch]
            assert len(watch) == len(to_watch), (len(watch), len(to_watch))
            tmp = {}
            for p, gs in to_watch:
                tmp[p] = set(gs)
            ps = sorted(tmp)
            print(f'[{classifier}] Nb. Groups:')
            for p in ps:
                print(f'\t{len(tmp[p])}\t{p}')
            print(f'[{classifier}] Common groups:')
            for i in range(len(ps)):
                for j in range(i + 1, len(ps)):
                    common = tmp[ps[i]] & tmp[ps[j]]
                    print(f'\t{len(tmp[ps[i]])}\t{ps[i]}')
                    print(f'\t{len(tmp[ps[j]])}\t{ps[j]}')
                    print(f'\t\t{len(common)}')

        it_output = iter(output)
        p, ig = next(it_output)
        ig = set(ig)
        all_groups = set(ig)
        min_g = max_g = len(ig)
        video_to_groups = {p: list(ig)}
        group_to_videos = {g: [p] for g in ig}
        nb_total_groups = 0
        for path, image_groups in it_output:
            image_groups = set(image_groups)
            all_groups.update(image_groups)
            min_g = min(min_g, len(image_groups))
            max_g = max(max_g, len(image_groups))
            nb_total_groups += len(image_groups)
            video_to_groups[path] = list(image_groups)
            for g in image_groups:
                group_to_videos.setdefault(g, []).append(path)

        all_groups = list(all_groups)
        assert len(video_to_groups) == len(videos)
        assert len(group_to_videos) == len(all_groups)
        print(f'Groups count: total {len(all_groups)} min {min_g} max {max_g} average {nb_total_groups / len(output)}')

        if display_extremums:
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

        vid_to_gid_to_s = {}
        for vid, b_to_s in vid_to_b_to_s.items():
            for b, s in b_to_s.items():
                vid_to_gid_to_s.setdefault(vid, {})[group_to_gid[b]] = s

        tasks = [(v, g) for v, g in vid_to_gid_s.items() if len(g)]
        vid_to_len = {v: len(g) for v, g in vid_to_gid_s.items()}
        jobs = functions.dispatch_tasks(
            tasks, cpu_count, [threshold, min_count, vid_to_len, gid_to_vid_s, vid_to_gid_to_s, DEFAULT_NOTIFIER])
        with Profiler('Async find similarities'):
            sub_results = functions.parallelize(job_find_similarities, jobs, cpu_count)
        results += sub_results

    weights = {}
    for similarities in results:
        for video_id, video_indices in similarities.items():
            for other_id, (a, b) in video_indices.items():
                key = (video_id, other_id)
                if key in weights:
                    u, v = weights[key]
                    if a / b > u / v:
                        weights[key] = (a, b)
                else:
                    weights[key] = (a, b)

    with Profiler('filter weights'):
        filtered_weights = {}
        for video_id, other_id in weights:
            if (other_id, video_id) in weights:
                h1, c1 = weights[(video_id, other_id)]
                h2, c2 = weights[(other_id, video_id)]
                if h1 / c1 < h2 / c2:
                    max_ratio = h2, c2
                else:
                    max_ratio = h1, c1
                filtered_weights[tuple(sorted((video_id, other_id)))] = max_ratio
        weights = filtered_weights

    # if duration_diff_seconds is not None:
    #     with Profiler(f'Filter with duration {duration_diff_seconds}'):
    #         selected_weights = {}
    #         for video_id, other_id in weights:
    #             if abs(vid_to_v[video_id].raw_seconds - vid_to_v[other_id].raw_seconds) <= duration_diff_seconds:
    #                 selected_weights[(video_id, other_id)] = weights[(video_id, other_id)]
    #         weights = selected_weights

    sim_graph = Graph()
    for video_id, other_id in weights:
        sim_graph.connect(video_id, other_id)

    sim_groups = []
    while sim_graph.edges:
        v, vs = sim_graph.edges.popitem()
        g = {v}
        while vs:
            ov = vs.pop()
            if ov not in g:
                g.add(ov)
                vs.update(sim_graph.edges.pop(ov))
        sim_groups.append(list(g))

    with Profiler('Refine similar groups'):
        refined_sim_groups = []
        for sim_group in sim_groups:
            if len(sim_group) == 2:
                refined_sim_groups.append(sim_group)
            else:
                indices_to_validate = list(sim_group)
                while indices_to_validate:
                    sub_group = [indices_to_validate.pop()]
                    other_indices = []
                    for other_id in indices_to_validate:
                        is_connected = True
                        for video_id in sub_group:
                            key = tuple(sorted((video_id, other_id)))
                            if key not in weights:
                                is_connected = False
                                break
                        if is_connected:
                            sub_group.append(other_id)
                        else:
                            other_indices.append(other_id)
                    if len(sub_group) > 1:
                        refined_sim_groups.append(sub_group)
                    indices_to_validate = other_indices
        print('Before', len(sim_groups), sum(len(g) for g in sim_groups))
        print('After', len(refined_sim_groups), sum(len(g) for g in refined_sim_groups))
        sim_groups = refined_sim_groups

    sim_groups.sort(key=lambda g: len(g), reverse=True)
    sim_vids = set()
    for gs in sim_groups:
        sim_vids.update(gs)
    assert len(sim_vids) == sum(len(sg) for sg in sim_groups), (len(sim_vids), sum(len(sg) for sg in sim_groups))

    if not debug:
        special_property = '__image__'
        DEFAULT_NOTIFIER.notify(notifications.Message('Create video property', special_property))
        if not api.database.has_prop_type(special_property):
            api.database.add_prop_type(PropType(special_property, '', True))
        DEFAULT_NOTIFIER.notify(notifications.Message('Clear video property', special_property))
        for video in videos:
            video.properties[special_property] = []

        s = int(1 + math.log10(len(sim_groups)))
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
            tag = f'{str(tag_id + 1).rjust(s, "0")} {" ".join(f"{s}({a}/{b})" for s, a, b in sorted(set(sir)))}'
            for video_id in similar_video_indices:
                vid_to_v[video_id].properties[special_property].extend([tag, '(similar)'])
        for video in videos:
            video.properties[special_property] = sorted(set(video.properties[special_property]))
        api.database.save()

    DEFAULT_NOTIFIER.notify(
        notifications.Message(f'Similar groups: {len(sim_groups)}, similar videos: {len(sim_vids)}, ratio {len(sim_vids) / len(sim_groups)}'))
    if return_groups:
        return sim_groups
    return len(sim_groups), len(sim_vids)


def main(files=None, expected_groups=None):
    # thresholds = (0.5, 0.6, 0.9)
    # min_counts = (5,)
    # color_points = (4, 6, 16, 18, 52, 86)
    # position_points = (4, 8, 10, 22)
    # size_points = (32, 34, 94, 342)
    # group_min_sizes = (4,)
    # px_dst_radius = (1, 2, 4)

    thresholds = (0.5,)
    min_counts = (5,)
    color_points = (4, 8, 16, 32, 64)
    position_points = (4, 8, 16)
    size_points = (8, 16, 32, 64, 128, 256)
    group_min_sizes = (1,)
    px_dst_radius = (8,)

    cases = list(itertools.product(
        reversed(thresholds),
        reversed(min_counts),
        reversed(color_points),
        reversed(position_points),
        reversed(size_points),
        reversed(group_min_sizes),
        reversed(px_dst_radius),
    ))
    from pysaurus.core.components import Duration
    print('Nb. of cases:', len(cases))
    print('Estimated total time:', Duration.from_minutes(len(cases) * 1.5))
    # exit(0)

    api = API(TEST_LIST_FILE_PATH, update=False)
    if files:
        videos = []
        for filename in files:
            video = api.database.get_video_from_filename(filename)
            assert video, filename
            videos.append(video)
    else:
        videos = list(api.database.readable.found.with_thumbnails) + list(
            api.database.readable.not_found.with_thumbnails)  # type: List[Video]
    videos_dict = {v.filename.path: v for v in videos}  # type: Dict[str, Video]
    vid_to_v = {v.video_id: v for v in videos}  # type: Dict[int, Video]
    min_dict = {m.identifier: m for m in api.database.ensure_miniatures(return_miniatures=True)}
    miniatures = [min_dict[video.filename.path] for video in videos]
    results = []
    assert expected_groups
    curr_nb_found = None
    curr_case = None
    curr_ratio = None
    for index_case, case in enumerate(cases):
        threshold, min_count, nb_color_points, nb_position_points, nb_size_points, group_min_size, pixel_distance_radius = case
        sim_groups = run(
            api, videos, videos_dict, vid_to_v, miniatures,
            threshold=threshold,
            min_count=min_count,
            nb_color_points=nb_color_points,
            nb_position_points=nb_position_points,
            nb_size_points=nb_size_points,
            group_min_size=group_min_size,
            pixel_distance_radius=pixel_distance_radius,
            group_classifier=('intervals', 'sub_intervals'),
            return_groups=True
        )
        sim_vids = set()
        path_to_group = {}
        for i, sim_group in enumerate(sim_groups):
            sim_vids.update(sim_group)
            for vid in sim_group:
                path_to_group[vid_to_v[vid].filename.path] = i
        ratio = len(sim_vids) / len(sim_groups)
        nb_found = 0
        nb_not_found = 0
        for i, expected_group in enumerate(expected_groups):
            found = {}
            for expected_path in expected_group:
                group_id = path_to_group.get(expected_path, -1)
                found.setdefault(group_id, []).append(expected_path)
            if len(found) == 1 and -1 not in found:
                nb_found += 1
            else:
                nb_not_found += 1
        print('Found', nb_found, 'not found', nb_not_found, (nb_found * 100) / (nb_found + nb_not_found), '%')
        if curr_nb_found is None:
            curr_nb_found = nb_found
            curr_case = case
            curr_ratio = ratio
            print('Initialized', nb_found, ratio, case)
        elif nb_found > curr_nb_found:
            curr_nb_found = nb_found
            curr_case = case
            curr_ratio = ratio
            print('Better', nb_found, ratio, case)
        else:
            print('Previous still better', curr_nb_found, curr_ratio, curr_case)
        results.append((ratio, len(sim_groups), len(sim_vids), nb_found, case))
        # if (index_case + 1) % 5 == 0:
        #     break

    results.sort()
    print('Final results:')
    for i, r in enumerate(results):
        ratio, nb_groups, nb_videos, nb_found, case = r
        print(f'[{i}] Ratio {ratio} Groups {nb_groups} Videos {nb_videos} Found {nb_found} Case {case}')


def unique_run(threshold, min_count, nb_color_points, nb_position_points, nb_size_points, group_min_size,
               pixel_distance_radius, group_classifier=None, expected_groups=None, watch=None):
    api = API(TEST_LIST_FILE_PATH, update=False)
    videos = list(api.database.readable.found.with_thumbnails) + list(
        api.database.readable.not_found.with_thumbnails)  # type: List[Video]
    videos_dict = {v.filename.path: v for v in videos}  # type: Dict[str, Video]
    vid_to_v = {v.video_id: v for v in videos}  # type: Dict[int, Video]
    min_dict = {m.identifier: m for m in api.database.ensure_miniatures(return_miniatures=True)}
    miniatures = [min_dict[video.filename.path] for video in videos]
    sim_groups = run(
        api, videos, videos_dict, vid_to_v, miniatures,
        threshold=threshold,
        min_count=min_count,
        nb_color_points=nb_color_points,
        nb_position_points=nb_position_points,
        nb_size_points=nb_size_points,
        group_min_size=group_min_size,
        pixel_distance_radius=pixel_distance_radius,
        debug=False,
        group_classifier=group_classifier,
        return_groups=True,
        watch=watch
    )
    if expected_groups:
        path_to_group = {}
        for i, sim_group in enumerate(sim_groups):
            for vid in sim_group:
                path_to_group[vid_to_v[vid].filename.path] = i
        nb_found = 0
        nb_not_found = 0
        for i, expected_group in enumerate(expected_groups):
            found = {}
            for expected_path in expected_group:
                group_id = path_to_group.get(expected_path, -1)
                found.setdefault(group_id, []).append(expected_path)
            if len(found) == 1 and -1 not in found:
                nb_found += 1
                # print('Found expected group', i + 1)
            else:
                nb_not_found += 1
                # print('** Not found expected groupe **', i + 1)
                # for gid, ps in found.items():
                #     for p in ps:
                #         print(f'\t{gid}\t{p}')
        print('Found', nb_found, 'not found', nb_not_found, (nb_found * 100) / (nb_found + nb_not_found), '%')


def observe(
        threshold,
        min_count,
        nb_color_points,
        nb_position_points,
        nb_size_points,
        group_min_size,
        pixel_distance_radius,
        files,
        *,
        group_classifier: Optional[str] = 'intervals',
        just_display_groups=True,
):
    api = API(TEST_LIST_FILE_PATH, update=False)

    videos = []
    for filename in files:
        video = api.database.get_video_from_filename(filename)
        assert video, filename
        videos.append(video)

    videos_dict = {v.filename.path: v for v in videos}  # type: Dict[str, Video]
    vid_to_v = {v.video_id: v for v in videos}  # type: Dict[int, Video]
    min_dict = {m.identifier: m for m in api.database.ensure_miniatures(return_miniatures=True)}
    miniatures = [min_dict[video.filename.path] for video in videos]

    run(
        api, videos, videos_dict, vid_to_v, miniatures,
        threshold=threshold,
        min_count=min_count,
        nb_color_points=nb_color_points,
        nb_position_points=nb_position_points,
        nb_size_points=nb_size_points,
        group_min_size=group_min_size,
        pixel_distance_radius=pixel_distance_radius,
        group_classifier=group_classifier,
        just_display_groups=just_display_groups,
    )


def _main():
    width = 32
    step = 8
    for y in range(32):
        for x in range(32):
            print(_categorize_position(x, y, width, step), end=' ')
        print()
    print()
    for y in range(32):
        for x in range(32):
            print(_categorize_sub_position(x, y, width, step), end=' ')
        print()
    print()
    for x in range(32):
        print(_categorize_value(x, step), end=' ')
    print()
    for x in range(32):
        print(_categorize_sub_value(x, step), end=' ')
    print()
    exit(0)


PRINT_STEP = 100
if __name__ == '__main__':
    # _main()
    with Profiler('Main function.'):
        example_files = [
            r"J:\donnees\divers\autres\p\[HD, 1920x1080p] Fucked and Oiled Up - Susy Gala  HD-Porn.me.mp4",
            r"Q:\donnees\autres\p\Susy Gala - Fucked And Oiled Up - Ready Or Not Here I Cum #bigtits.mp4",
            r"Q:\donnees\autres\p\Susy Gala - Nacho's First Class Fucks (2016) #POV.mp4",
            r"J:\donnees\divers\autres\p\Hannah Hays - Biggest Black Cock - XFREEHD.mp4",
            r"M:\donnees\autres\p\Hannah Hays - Interracial Pickups.mp4",
            r"Q:\donnees\autres\p\Hannah Hays_2.mp4",
            r"J:\donnees\divers\autres\p\Daya Knight - black teacher helping little boy study - 1080.mp4",
            r"L:\donnees\autres\p\Daya Knight - bkb16158-1080p.mp4",
            r"M:\donnees\autres\p\daya knight - Young Guy Fucks Ebony Lady.mp4",
        ]
        similarity_filename = r"C:\data\git\.local\.html\similarities.json"
        groups = []
        files = []
        with open(similarity_filename) as file:
            _similarities = json.load(file)
        for group in _similarities:
            local_files = []
            for file in group:
                if AbsolutePath.ensure(group[file]).isfile():
                    local_files.append(file)
            if len(local_files) > 1:
                groups.append(local_files)
                files.extend(local_files)
        print('Expected similarities', len(groups), 'Files', len(files), len(files) / len(groups))
        # main(expected_groups=groups)
        # unique_run(0.5, 5, 4, 4, 32, 4, 4, group_classifier=('intervals', 'sub_intervals'))
        # observe(0.5, 5, 4, 4, 34, 4, 4, files=files, group_classifier=None, just_display_groups=False)
        # ?
        # unique_run(0.5, 5, 8, 4, 8, 4, 4, group_classifier=('intervals', 'sub_intervals'))
        # good
        # unique_run(0.5, 5, 8, 4, 8, 4, 4, group_classifier=('intervals', 'sub_intervals'))
        # unique_run(0.5, 5, 8, 4, 32, 4, 2, group_classifier=('intervals', 'sub_intervals'))

        # watch = [
        #     r"E:\donnees\autres\p\busty-asian-real-estate-agent-gets-her-pussy-destroyed_1080p.mp4",
        #     r"J:\donnees\divers\autres\p\Mena Li and a big black cock__p720.mp4",
        #     r"M:\donnees\autres\p\mena li - Asian pussy gets destroyed with a BBC__p720.mp4",
        #     r"R:\donnees\autres\p\mena li - Scene 2 From Chocolate Desires - 1080p.mp4",
        # ]
        unique_run(
            threshold=0.5,
            min_count=0,
            #
            group_min_size=1,
            nb_color_points=8,
            nb_position_points=4,
            nb_size_points=4,
            pixel_distance_radius=6,
            #
            group_classifier=('intervals', 'sub_intervals'),
            expected_groups=groups,
            # watch=watch
        )
        print('Expected similarities', len(groups), 'Files', len(files), len(files) / len(groups))
