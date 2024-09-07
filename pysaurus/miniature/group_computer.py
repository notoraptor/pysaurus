from typing import List

from pysaurus.core.classes import AbstractMatrix
from pysaurus.core.graph import Graph
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.core.parallelization import USABLE_CPU_COUNT, parallelize
from pysaurus.core.profiling import Profiler
from pysaurus.miniature.decomposed_miniature import DecomposedMiniature
from pysaurus.miniature.miniature import Miniature
from pysaurus.miniature.pixel_comparator import DistancePixelComparator
from pysaurus.miniature.pixel_group import PixelGroup
from saurus.language import say


class GroupComputer:
    __slots__ = (
        "group_min_size",
        "pixel_comparator",
        "print_step",
        "similarity",
        "radius",
    )

    def __init__(
        self,
        *,
        group_min_size,
        similarity_percent=None,
        pixel_distance_radius: int = None,
        print_step=500,
        normalizer=0,
    ):
        assert (similarity_percent is None) ^ (pixel_distance_radius is None)
        if pixel_distance_radius is not None:
            similarity_percent = self.compute_similarity_percent(pixel_distance_radius)
        self.similarity = similarity_percent
        self.radius = pixel_distance_radius
        self.group_min_size = group_min_size
        self.pixel_comparator = DistancePixelComparator(similarity_percent, normalizer)
        self.print_step = print_step

    @classmethod
    def compute_similarity_percent(cls, pixel_distance_radius: int) -> float:
        return (255 - pixel_distance_radius) * 100 / 255

    def batch_compute_groups(
        self, miniatures: List[Miniature], *, notifier=DEFAULT_NOTIFIER
    ) -> List[DecomposedMiniature]:
        with Profiler(
            say("batch_compute_groups(n={n} miniature(s))", n=len(miniatures)), notifier
        ):
            raw_output = list(
                parallelize(
                    self.collect_miniature_groups,
                    miniatures,
                    cpu_count=USABLE_CPU_COUNT,
                    notifier=notifier,
                    kind="miniature(s)",
                )
            )
        return raw_output

    def collect_miniature_groups(self, miniature) -> DecomposedMiniature:
        return DecomposedMiniature(miniature.identifier, self.group_pixels(miniature))

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
