from typing import List

from pysaurus.core.database import notifications
from pysaurus.other.tests.image_management.graph import Graph
from pysaurus.other.tests.image_management.pixel_comparator import DistancePixelComparator
from pysaurus.other.tests.image_management.pixel_group import PixelGroup


class GroupComputer:
    __slots__ = "group_min_size", "pixel_comparator", "print_step"

    def __init__(self, *, group_min_size, similarity_percent, print_step=500):
        self.group_min_size = group_min_size
        self.pixel_comparator = DistancePixelComparator(similarity_percent)
        self.print_step = print_step

    def group_pixels(self, raw_data, width, height) -> List[PixelGroup]:
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

    def compute_groups(self, miniature) -> List[PixelGroup]:
        # compute_groups
        return [
            group
            for group in self.group_pixels(
                miniature.data(), miniature.width, miniature.height
            )
            if len(group.members) >= self.group_min_size
        ]

    def async_compute(self, context):
        index_task, miniature, nb_all_tasks, notifier = context
        if (index_task + 1) % self.print_step == 0:
            notifier.notify(notifications.VideoJob("", index_task + 1, nb_all_tasks))
        return miniature.identifier, self.compute_groups(miniature)
