import tkinter as tk
from typing import List, Tuple, Dict, Set, Any, Union

from PIL import Image, ImageTk

from pysaurus.core import functions
from pysaurus.core.modules import ImageUtils, ColorUtils
from pysaurus.core.database.api import API
from pysaurus.core.database.video import Video
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH


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

    __slots__ = 'length', 'points', 'nb_points', 'l'

    @classmethod
    def _space_between_points(cls, interval_length, nb_points):
        # 2 <= k < interval_length
        top = interval_length - nb_points
        bottom = nb_points - 1
        if top % (2 * bottom):
            return None
        return top // bottom

    @classmethod
    def _available_points_and_spaces(cls, interval_length):
        pt_to_il = {}
        for pt in range(2, interval_length):
            il = cls._space_between_points(interval_length, pt)
            if il:
                pt_to_il[pt] = il
        return pt_to_il

    def __init__(self, length=256, nb_points=6):
        points = self._available_points_and_spaces(length)
        assert nb_points in points, tuple(points)
        self.length = length
        self.points = points
        self.nb_points = nb_points
        self.l = self.points[self.nb_points]

    def nearest_point(self, value: int):
        # 0 <= value < interval length
        i = value // (self.l + 1)
        before = i * (self.l + 1)
        after = (i + 1) * (self.l + 1)
        if value - before < after - value:
            return before
        return after

    def nearest_points(self, values: Union[List[int], Tuple[int]]):
        return type(values)(self.nearest_point(value) for value in values)


class Display:

    @staticmethod
    def from_path(path):
        root = tk.Tk()
        img = Image.open(path)
        tk_image = ImageTk.PhotoImage(img)
        label = tk.Label(master=root)
        label["image"] = tk_image
        label.pack(side="left")
        root.mainloop()

    @staticmethod
    def from_images(*images):
        root = tk.Tk()
        tk_images = []
        for img in images:
            tk_image = ImageTk.PhotoImage(img)
            tk_images.append(tk_image)
            tk.Label(master=root, image=tk_image).pack(side="left")
            print(img.mode, *img.size)
        root.mainloop()


class Graph:
    __slots__ = 'edges',

    def __init__(self):
        self.edges = {}  # type: Dict[Any, Set[Any]]

    def connect(self, a, b):
        self.edges.setdefault(a, set()).add(b)
        self.edges.setdefault(b, set()).add(a)


class Grid:
    __slots__ = 'data', 'width', 'height'

    def __init__(self, data: List[Tuple[int, int, int]], width: int, height: int):
        self.data = data
        self.width = width
        self.height = height


class Group:
    __slots__ = 'grid', 'identifier', 'members', 'connections'

    def __init__(self, grid: Grid, identifier: int, members: Set[int]):
        self.grid = grid
        self.identifier = identifier
        self.members = members
        self.connections = set()  # type: Set[Group]

    def __str__(self):
        return (
            f"Group({self.identifier + 1} "
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
    def size(self):
        return len(self.members)

    @property
    def color(self):
        return self.grid.data[next(iter(self.members))]

    @property
    def center(self):
        nb_points = len(self.members)
        total_x = 0
        total_y = 0
        for identifier in self.members:
            x, y = functions.flat_to_coord(identifier, self.grid.width)
            total_x += x
            total_y += y
        return total_x / nb_points, total_y / nb_points

    @property
    def edges(self):
        for other in self.connections:
            yield Arrow(self, other)


class Arrow:
    __slots__ = 'from_color', 'to_color', 'rank', 'category'

    GREATER = '>'
    SMALLER = '<'
    EQUALS = '='

    @classmethod
    def categorize_angle(cls, degrees):
        """Return nearest multiple of 45 degrees to given degrees."""
        index_before = int(degrees // 45)
        angle_before = index_before * 45
        angle_after = (index_before + 1) * 45
        if (degrees - angle_before) < (angle_after - degrees):
            return angle_before
        return angle_after % 360

    def __init__(self, a: Group, b: Group):
        size_a = a.size
        size_b = b.size
        if size_a // size_b > 1:
            rank = self.GREATER
        elif size_b // size_a > 1:
            rank = self.SMALLER
        else:
            rank = self.EQUALS
        angle = functions.get_vector_angle(a.center, b.center)
        self.from_color = a.color
        self.rank = rank
        self.category = self.categorize_angle(angle)
        self.to_color = b.color

    def __str__(self):
        return f"{ColorUtils.rgb_to_hex(self.from_color)}{self.rank}{self.category}{ColorUtils.rgb_to_hex(self.to_color)}"


def segment_image(grid: Grid):
    """Column to right, row to bottom"""
    graph = Graph()
    disconnected = Graph()
    # Connect pixels in first line.
    for current_index in range(1, grid.width):
        previous_index = current_index - 1
        if grid.data[previous_index] == grid.data[current_index]:
            graph.connect(current_index, previous_index)
        else:
            disconnected.connect(current_index, previous_index)
    # Connect pixels in next lines.
    for y in range(1, grid.height):
        # Connect first pixel.
        current_index = y * grid.width
        above_index = current_index - grid.width
        if grid.data[current_index] == grid.data[above_index]:
            graph.connect(current_index, above_index)
        else:
            disconnected.connect(current_index, above_index)
        # Connect next pixels.
        for x in range(1, grid.width):
            current_index = y * grid.width + x
            above_index = current_index - grid.width
            previous_index = current_index - 1
            if grid.data[current_index] == grid.data[above_index]:
                graph.connect(current_index, above_index)
            else:
                disconnected.connect(current_index, above_index)
            if grid.data[current_index] == grid.data[previous_index]:
                graph.connect(current_index, previous_index)
            else:
                disconnected.connect(current_index, previous_index)
    # Get groups and connect each pixel to its group.
    groups = []  # type: List[Group]
    index_to_group = [-1] * grid.width * grid.height
    while graph.edges:
        group_id = len(groups)
        index, other_indices = graph.edges.popitem()
        group = {index}
        index_to_group[index] = group_id
        while other_indices:
            other_index = other_indices.pop()
            if other_index not in group:
                group.add(other_index)
                index_to_group[other_index] = group_id
                other_indices.update(graph.edges.pop(other_index))
        groups.append(Group(grid, group_id, group))
    # Connect groups.
    for in_index, out_indices in disconnected.edges.items():
        for out_index in out_indices:
            id_group_in = index_to_group[in_index]
            id_group_out = index_to_group[out_index]
            if id_group_in >= 0 and id_group_out >= 0:
                groups[id_group_in].connections.add(groups[id_group_out])
    # retain only groups with at least 3 members.
    final_groups = [group for group in groups if len(group.members) > 2]
    for group in final_groups:
        print(group)
        for edge in group.edges:
            print(f"\t{edge}")
    # Display number of groups.
    print('Number of pixels:', grid.width * grid.height)
    print('Number of colors', len(set(grid.data)))
    print('Number of groups:', len(groups))
    print('Number of final groups:', len(final_groups))
    return final_groups


def main():
    spaced_points = SpacedPoints()
    api = API(TEST_LIST_FILE_PATH, update=False)
    videos = sorted(api.database.readable.found.with_thumbnails)  # type: List[Video]
    video = videos[3]

    miniatures = api.database.ensure_miniatures(return_miniatures=True)
    min_dict = {m.identifier: m for m in miniatures}
    miniature = min_dict[video.filename.path]
    img = ImageUtils.new_rgb_image(list(miniature.data()), miniature.width, miniature.height)
    # Categorize pixels.
    output_data = [spaced_points.nearest_points(pixel) for pixel in img.getdata()]
    grid = Grid(output_data, *img.size)
    segment_image(grid)
    # Display.from_images(
    #     img,
    #     ImageUtils.new_rgb_image(output_data, *img.size),
    #     ImageUtils.new_rgb_image(segment_image(grid), *img.size),
    # )


if __name__ == '__main__':
    main()
