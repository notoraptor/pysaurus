from multiprocessing import Pool
from typing import List

from pysaurus.core import notifications
from pysaurus.core.classes import AbstractMatrix
from pysaurus.core.constants import CPU_COUNT
from pysaurus.core.miniature_tools.decomposed_miniature import (
    DecomposedMiniature,
)
from pysaurus.core.miniature_tools.graph import Graph
from pysaurus.core.miniature_tools.miniature import Miniature
from pysaurus.core.miniature_tools.pixel_comparator import (
    DistancePixelComparator,
)
from pysaurus.core.miniature_tools.pixel_group import PixelGroup
from pysaurus.core.notifier import DEFAULT_NOTIFIER
from pysaurus.core.profiling import Profiler


class GroupComputer:
    __slots__ = (
        "group_min_size",
        "pixel_comparator",
        "print_step",
        "similarity",
        "radius",
    )

    @classmethod
    def compute_similarity_percent(cls, pixel_distance_radius: int) -> float:
        return (255 - pixel_distance_radius) * 100 / 255

    def __init__(
        self,
        *,
        group_min_size,
        similarity_percent=None,
        pixel_distance_radius: int = None,
        print_step=500,
    ):
        assert (similarity_percent is None) ^ (pixel_distance_radius is None)
        if pixel_distance_radius is not None:
            similarity_percent = self.compute_similarity_percent(pixel_distance_radius)
        self.similarity = similarity_percent
        self.radius = pixel_distance_radius
        self.group_min_size = group_min_size
        self.pixel_comparator = DistancePixelComparator(similarity_percent)
        self.print_step = print_step

    def group_pixels(self, miniature: AbstractMatrix) -> List[PixelGroup]:
        width = miniature.width
        data = self.pixel_comparator.normalize_data(miniature.data(), width)
        graph = Graph()
        # Connect pixels in first line.
        for current_index in range(1, width):
            previous_index = current_index - 1
            if self.pixel_comparator.pixels_are_close(
                data, current_index, previous_index, width
            ):
                graph.connect(current_index, previous_index)
        # Connect pixels in next lines.
        for y in range(1, miniature.height):
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
        return [
            PixelGroup(
                self.pixel_comparator.common_color(data, group, width),
                width,
                group_id,
                group,
            )
            for group_id, group in enumerate(graph.pop_groups())
            if len(group) >= self.group_min_size
        ]

    def async_compute(self, context) -> DecomposedMiniature:
        jobn: notifications.JobNotifications
        index_task, miniature, nb_all_tasks, jobn = context
        if (index_task + 1) % self.print_step == 0:
            jobn.progress(None, index_task + 1, nb_all_tasks)
        return DecomposedMiniature(miniature.identifier, self.group_pixels(miniature))

    def batch_compute_groups(
        self, miniatures: List[Miniature], *, notifier=None, cpu_count=None
    ) -> List[DecomposedMiniature]:
        cpu_count = cpu_count or max(1, CPU_COUNT - 2)
        notifier = notifier or DEFAULT_NOTIFIER
        jobn = notifications.Jobs.group_computer(len(miniatures), notifier)
        tasks = [(i, m, len(miniatures), jobn) for i, m in enumerate(miniatures)]
        with Profiler(f"batch_compute_groups(n={len(tasks)}, cpu={cpu_count})"):
            with Pool(cpu_count) as p:
                raw_output = list(p.imap(self.async_compute, tasks))
        jobn.progress(None, len(miniatures), len(miniatures))
        return raw_output
