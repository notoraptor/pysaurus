import os
from multiprocessing import Pool
from typing import List, Iterable, Tuple

from pysaurus.core.database import notifications
from pysaurus.core.miniature import Miniature
from pysaurus.core.notification import DEFAULT_NOTIFIER
from pysaurus.core.profiling import Profiler
from pysaurus.other.tests.image_management.elements.decomposed_miniature import (
    DecomposedMiniature,
)
from pysaurus.other.tests.image_management.elements.graph import Graph
from pysaurus.other.tests.image_management.elements.pixel_comparator import (
    DistancePixelComparator,
)
from pysaurus.other.tests.image_management.elements.pixel_group import PixelGroup


class GroupComputer:
    __slots__ = "group_min_size", "pixel_comparator", "print_step", "similarity", "radius"

    @classmethod
    def compute_similarity_percent(cls, pixel_distance_radius: int) -> float:
        return (255 - pixel_distance_radius) * 100 / 255

    def __init__(self, *, group_min_size, similarity_percent=None, pixel_distance_radius: int = None, print_step=2000):
        assert (similarity_percent is None) ^ (pixel_distance_radius is None)
        if pixel_distance_radius is not None:
            similarity_percent = self.compute_similarity_percent(pixel_distance_radius)
        self.similarity = similarity_percent
        self.radius = pixel_distance_radius
        self.group_min_size = group_min_size
        self.pixel_comparator = DistancePixelComparator(similarity_percent)
        self.print_step = print_step

    def group_pixels(
        self, raw_data: Iterable[Tuple[int, int, int]], width: int, height: int
    ) -> List[PixelGroup]:
        data = self.pixel_comparator.normalize_data(raw_data, width)
        graph = Graph()
        # Connect pixels in first line.
        for current_index in range(1, width):
            previous_index = current_index - 1
            if self.pixel_comparator.pixels_are_close(
                data, current_index, previous_index, width
            ):
                graph.connect(current_index, previous_index)
        # Connect pixels in next lines.
        for y in range(1, height):
            # Connect first pixel.
            current_index = y * width
            above_index = current_index - width
            if self.pixel_comparator.pixels_are_close(
                data, current_index, above_index, width
            ):
                graph.connect(current_index, above_index)
            # Connect next pixels.
            for x in range(1, width):
                current_index = y * width + x
                above_index = current_index - width
                previous_index = current_index - 1
                top_left_index = current_index - width - 1
                if self.pixel_comparator.pixels_are_close(
                    data, current_index, above_index, width
                ):
                    graph.connect(current_index, above_index)
                if self.pixel_comparator.pixels_are_close(
                    data, current_index, previous_index, width
                ):
                    graph.connect(current_index, previous_index)
                if self.pixel_comparator.pixels_are_close(
                    data, current_index, top_left_index, width
                ):
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
            groups.append(
                PixelGroup(
                    self.pixel_comparator.common_color(data, group, width),
                    width,
                    group_id,
                    group,
                )
            )
        return groups

    def compute_groups(self, miniature: Miniature) -> List[PixelGroup]:
        # compute_groups
        return [
            group
            for group in self.group_pixels(
                miniature.data(), miniature.width, miniature.height
            )
            if len(group.members) >= self.group_min_size
        ]

    def async_compute(self, context) -> DecomposedMiniature:
        index_task, miniature, nb_all_tasks, notifier = context
        if (index_task + 1) % self.print_step == 0:
            notifier.notify(notifications.MiniatureGroupComputerJob(None, index_task + 1, nb_all_tasks))
        return DecomposedMiniature(miniature.identifier, self.compute_groups(miniature))

    def batch_compute_groups(
        self, miniatures: List[Miniature], *, notifier=None, cpu_count=None
    ) -> List[DecomposedMiniature]:
        cpu_count = cpu_count or max(1, os.cpu_count() - 2)
        notifier = notifier or DEFAULT_NOTIFIER
        tasks = [(i, m, len(miniatures), notifier) for i, m in enumerate(miniatures)]
        with Profiler(f"batch_compute_groups(n={len(tasks)}, cpu={cpu_count})"):
            with Pool(cpu_count) as p:
                raw_output = list(p.imap(self.async_compute, tasks))
        return raw_output
