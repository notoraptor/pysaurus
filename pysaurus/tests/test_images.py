from abc import ABC, abstractmethod
import tkinter as tk
from typing import List, Tuple, Optional, Dict, Set, Any

from PIL import Image, ImageTk

from pysaurus.core import functions
from pysaurus.core.database.api import API
from pysaurus.core.database.video import Video
from pysaurus.core.native.video_raptor.miniature import Miniature
from pysaurus.tests.test_utils import TEST_LIST_FILE_PATH


def space_between_points(interval_length, nb_points):
    # 2 <= k < interval_length
    top = interval_length - nb_points
    bottom = nb_points - 1
    if top % (2 * bottom):
        return None
    return top // bottom


def available_points_and_spaces(interval_length):
    pt_to_il = {}
    for pt in range(2, interval_length):
        il = space_between_points(interval_length, pt)
        if il:
            pt_to_il[pt] = il
    return pt_to_il


INTERVAL_LENGTH = 256
POINTS = available_points_and_spaces(INTERVAL_LENGTH)
# k = 2;  c = 8;      l = 254
# k = 4;  c = 64;     l = 84
# k = 6;  c = 216;    l = 50
# k = 16; c = 4096;   l = 16
# k = 18; c = 5832;   l = 14
# k = 52; c = 140608; l = 4
# k = 86; c = 636056; l = 2
DEFAULT_NB_POINTS = 6


def categorize_value(value: int, nb_points: int = DEFAULT_NB_POINTS):
    # 0 <= value < INTERVAL_LENGTH
    l = POINTS[nb_points]
    i = value // (l + 1)
    before = i * (l + 1)
    after = (i + 1) * (l + 1)
    if value - before < after - value:
        return before
    return after


def categorize_pixel(pixel: Tuple[int, int, int], nb_points: int = DEFAULT_NB_POINTS):
    return tuple(categorize_value(value, nb_points) for value in pixel)


def new_rgb_image(data, width, height):
    image = Image.new('RGB', (width, height))
    image.putdata(data)
    return image


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


class ColorIterator:
    def __init__(self, step=1):
        assert 256 % step == 0
        start = step - 1
        self.step = step
        self.r = start
        self.g = start
        self.b = start

    def is_white(self):
        return self.r == self.g == self.b == 255

    def next(self):
        current = self.r, self.g, self.b
        self.b += self.step
        if self.b // 256:
            self.b %= 256
            self.g += self.step
            if self.g // 256:
                self.g %= 256
                self.r += self.step
                if self.r // 256:
                    self.r %= 256
        return current


class __Way(ABC):
    __slots__ = 'width', 'height', 'row', 'col'

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.row = None
        self.col = None
        self.init()

    def to_index(self, coordinates):
        return functions.coord_to_flat(*coordinates, self.width)

    def current(self):
        return self.col, self.row

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    @abstractmethod
    def init(self):
        raise NotImplementedError()

    @abstractmethod
    def last(self):
        raise NotImplementedError()

    @abstractmethod
    def before(self):
        raise NotImplementedError()

    @abstractmethod
    def after(self):
        raise NotImplementedError()

    @abstractmethod
    def above(self):
        raise NotImplementedError()

    @abstractmethod
    def increment(self):
        raise NotImplementedError()


class WayRightBottom(__Way):
    """Column to right, row to bottom"""

    def before(self):
        return self.col - 1, self.row

    def after(self):
        return self.col + 1, self.row

    def above(self):
        return self.col, self.row - 1

    def init(self):
        self.row = 0
        self.col = 0

    def last(self):
        return self.width - 1, self.height - 1

    def increment(self):
        self.col = (self.col + 1) % self.width
        self.row = self.row + (not self.col)


class WayLeftTop(__Way):
    """Column to left, row to top"""
    def init(self):
        self.row = self.height - 1
        self.col = self.width - 1

    def last(self):
        return 0, 0

    def before(self):
        return self.col + 1, self.row

    def after(self):
        return self.col - 1, self.row

    def above(self):
        return self.col, self.row + 1

    def increment(self):
        self.col = (self.width + self.col - 1) % self.width
        self.row = self.row - (self.col == self.width - 1)


class WayBottomRight(__Way):
    """Column to bottom, row to right"""
    def init(self):
        self.row = 0
        self.col = 0

    def last(self):
        return self.width - 1, self.height - 1

    def before(self):
        return self.col, self.row - 1

    def after(self):
        return self.col, self.row + 1

    def above(self):
        return self.col - 1, self.row

    def increment(self):
        self.row = (self.row + 1) % self.height
        self.col = self.col + (not self.row)

    def get_width(self):
        return self.height

    def get_height(self):
        return self.width


class WayTopLeft(__Way):
    """Column to top, row to left"""
    def init(self):
        self.row = self.height - 1
        self.col = self.width - 1

    def last(self):
        return 0, 0

    def before(self):
        return self.col, self.row + 1

    def after(self):
        return self.col, self.row - 1

    def above(self):
        return self.col + 1, self.row

    def increment(self):
        self.row = (self.height + self.row - 1) % self.height
        self.col = self.col - (self.row == self.height - 1)

    def get_width(self):
        return self.height

    def get_height(self):
        return self.width


class Identifier:
    __slots__ = '__identifier',

    def __init__(self):
        self.__identifier = -1

    def next(self, prefix=None):
        self.__identifier += 1
        if prefix is None:
            return self.__identifier
        return f"{prefix}[{self.__identifier}]"


class Pending:
    __slots__ = 'index'
    def __init__(self, index):
        self.index = index


class Graph:
    __slots__ = 'edges',

    def __init__(self):
        self.edges = {}  # type: Dict[Any, Set[Any]]

    def connect(self, a, b):
        self.edges.setdefault(a, set()).add(b)
        self.edges.setdefault(b, set()).add(a)


def resolve_pending(arr, index, identifier: Identifier):
    pending = arr[index]
    assert isinstance(pending, Pending), type(pending)
    if pending.index == index:
        arr[index] = identifier.next('pending')
    else:
        foreign = arr[pending.index]
        if isinstance(foreign, str):
            arr[index] = foreign
        else:
            arr[index] = resolve_pending(arr, pending.index, identifier)
    return arr[index]


def segment_image_1(data, width, height):
    """Column to right, row to bottom"""
    identifier = Identifier()
    combined_groups = []
    for _ in range(width * height):
        combined_groups.append(set())

    for way in (WayRightBottom(width, height),
                WayLeftTop(width, height),
                WayBottomRight(width, height),
                WayTopLeft(width, height)):
        groups = [-1] * (width * height)
        # Set group for first column in first line.
        groups[way.to_index(way.current())] = identifier.next(type(way).__name__)
        # Set groups for next columns in first line.
        for _ in range(1, way.get_width()):
            way.increment()
            current_index = way.to_index(way.current())
            previous_index = way.to_index(way.before())
            if data[previous_index] == data[current_index]:
                groups[current_index] = groups[previous_index]
            else:
                groups[current_index] = identifier.next(type(way).__name__)
        # Set group for next lines.
        for _ in range(1, way.get_height()):
            # Set group for first column.
            way.increment()
            current_index = way.to_index(way.current())
            above_index = way.to_index(way.above())
            if data[current_index] == data[above_index]:
                groups[current_index] = groups[above_index]
            else:
                groups[current_index] = identifier.next(type(way).__name__)
            # Set group for next columns.
            for _ in range(1, way.get_width()):
                way.increment()
                current_index = way.to_index(way.current())
                previous_index = way.to_index(way.before())
                above_index = way.to_index(way.above())
                if data[current_index] == data[above_index]:
                    groups[current_index] = groups[above_index]
                elif data[current_index] == data[previous_index]:
                    groups[current_index] = groups[previous_index]
                else:
                    groups[current_index] = identifier.next(type(way).__name__)
        assert way.current() == way.last(), (way.current(), way.last())
        # Transfer groups from this way to combined groups for all ways.
        for index in range(len(groups)):
            combined_groups[index].add(groups[index])

    group_identifiers = []
    edges = {}  # type: Dict[int, Set[int]]
    for group_set in combined_groups:
        group_identifiers.append(tuple(sorted(group_set)))

    # Edges ====
    # first line
    for i in range(1, width):
        if group_identifiers[i] == group_identifiers[i - 1]:
            edges.setdefault(i, set()).add(i - 1)
            edges.setdefault(i - 1, set()).add(i)
    # next lines
    for y in range(1, height):
        # first column
        current_index = functions.coord_to_flat(0, y, width)
        above_index = functions.coord_to_flat(0, y - 1, width)
        if group_identifiers[current_index] == group_identifiers[above_index]:
            edges.setdefault(current_index, set()).add(above_index)
            edges.setdefault(above_index, set()).add(current_index)
        # next column
        for x in range(1, width):
            current_index = functions.coord_to_flat(x, y, width)
            previous_index = functions.coord_to_flat(x - 1, y, width)
            above_index = functions.coord_to_flat(x, y - 1, width)
            if group_identifiers[current_index] == group_identifiers[above_index]:
                edges.setdefault(current_index, set()).add(above_index)
                edges.setdefault(above_index, set()).add(current_index)
            if group_identifiers[current_index] == group_identifiers[previous_index]:
                edges.setdefault(current_index, set()).add(previous_index)
                edges.setdefault(previous_index, set()).add(current_index)

    # Get groups
    final_groups = []
    while edges:
        index = next(iter(edges))
        group = {index}
        other_indices = edges.pop(index)
        while other_indices:
            other_index = other_indices.pop()
            if other_index not in group:
                group.add(other_index)
                other_indices.update(edges.pop(other_index))
        identifiers = set(group_identifiers[i] for i in group)
        assert len(identifiers) == 1, len(identifiers)
        final_groups.append(group)

    # Display number of groups.
    print('Number of pixels:', width * height, len(set(data)))
    print('Number of groups:', len(final_groups))

    color_iterator = ColorIterator(2 ** 6)
    group_to_color = [color_iterator.next() for _ in range(len(final_groups))]
    position_to_color = [(0, 0, 0)] * width * height
    for group_id, group in enumerate(final_groups):
        color = group_to_color[group_id]
        for identifier in group:
            position_to_color[identifier] = color
    return position_to_color


def segment_image_2(data, width, height):
    """Column to right, row to bottom"""
    identifier = Identifier()
    combined_groups = []
    for _ in range(width * height):
        combined_groups.append(set())

    for way in (WayRightBottom(width, height),
                WayLeftTop(width, height),
                WayBottomRight(width, height),
                WayTopLeft(width, height)):
        groups = [None] * (width * height)
        # Set group for first column in first line.
        groups[way.to_index(way.current())] = identifier.next(type(way).__name__)
        # Set groups for next columns in first line.
        for _ in range(1, way.get_width()):
            way.increment()
            current_index = way.to_index(way.current())
            previous_index = way.to_index(way.before())
            if data[previous_index] == data[current_index]:
                groups[current_index] = groups[previous_index]
            else:
                groups[current_index] = identifier.next(type(way).__name__)
        # Set group for next lines.
        for _ in range(1, way.get_height()):
            # Set group for first column.
            way.increment()
            current_index = way.to_index(way.current())
            above_index = way.to_index(way.above())
            if data[current_index] == data[above_index]:
                groups[current_index] = groups[above_index]
            else:
                groups[current_index] = identifier.next(type(way).__name__)
            # Set group for next columns.
            for x in range(1, way.get_width()):
                way.increment()
                current_index = way.to_index(way.current())
                previous_index = way.to_index(way.before())
                above_index = way.to_index(way.above())
                if data[current_index] == data[above_index]:
                    groups[current_index] = groups[above_index]
                elif data[current_index] == data[previous_index]:
                    groups[current_index] = groups[previous_index]
                else:
                    g = None
                    if x < way.get_width() - 1:
                        after_index = way.to_index(way.after())
                        if data[current_index] == data[after_index]:
                            if groups[after_index] is None:
                                g = Pending(after_index)
                            else:
                                g = groups[after_index]
                    if g is None:
                        g = identifier.next(type(way).__name__)
                    groups[current_index] = g
        assert way.current() == way.last(), (way.current(), way.last())
        # Resolve pending.
        for i, group in enumerate(groups):
            if not isinstance(group, str):
                resolve_pending(groups, i, identifier)
                assert isinstance(groups[i], str)
        # Transfer groups from this way to combined groups for all ways.
        for index in range(len(groups)):
            combined_groups[index].add(groups[index])

    group_identifiers = []
    edges = {}  # type: Dict[int, Set[int]]
    for group_set in combined_groups:
        group_identifiers.append(tuple(sorted(group_set)))

    # Edges ====
    # first line
    for i in range(1, width):
        if group_identifiers[i] == group_identifiers[i - 1]:
            edges.setdefault(i, set()).add(i - 1)
            edges.setdefault(i - 1, set()).add(i)
    # next lines
    for y in range(1, height):
        # first column
        current_index = functions.coord_to_flat(0, y, width)
        above_index = functions.coord_to_flat(0, y - 1, width)
        if group_identifiers[current_index] == group_identifiers[above_index]:
            edges.setdefault(current_index, set()).add(above_index)
            edges.setdefault(above_index, set()).add(current_index)
        # next column
        for x in range(1, width):
            current_index = functions.coord_to_flat(x, y, width)
            previous_index = functions.coord_to_flat(x - 1, y, width)
            above_index = functions.coord_to_flat(x, y - 1, width)
            if group_identifiers[current_index] == group_identifiers[above_index]:
                edges.setdefault(current_index, set()).add(above_index)
                edges.setdefault(above_index, set()).add(current_index)
            if group_identifiers[current_index] == group_identifiers[previous_index]:
                edges.setdefault(current_index, set()).add(previous_index)
                edges.setdefault(previous_index, set()).add(current_index)

    # Get groups
    final_groups = []
    while edges:
        index = next(iter(edges))
        group = {index}
        other_indices = edges.pop(index)
        while other_indices:
            other_index = other_indices.pop()
            if other_index not in group:
                group.add(other_index)
                other_indices.update(edges.pop(other_index))
        identifiers = set(group_identifiers[i] for i in group)
        assert len(identifiers) == 1, len(identifiers)
        final_groups.append(group)

    # Display number of groups.
    print('Number of pixels:', width * height, len(set(data)))
    print('Number of groups:', len(final_groups))

    color_iterator = ColorIterator(2 ** 6)
    group_to_color = [color_iterator.next() for _ in range(len(final_groups))]
    position_to_color = [(0, 0, 0)] * width * height
    for group_id, group in enumerate(final_groups):
        color = group_to_color[group_id]
        for identifier in group:
            position_to_color[identifier] = color
    return position_to_color


def segment_image_3(data, width, height):
    """Column to right, row to bottom"""
    graph = Graph()

    for way in (WayRightBottom(width, height),
                WayLeftTop(width, height),
                WayBottomRight(width, height),
                WayTopLeft(width, height)):
        # Set groups for next columns in first line.
        for _ in range(1, way.get_width()):
            way.increment()
            current_index = way.to_index(way.current())
            previous_index = way.to_index(way.before())
            if data[previous_index] == data[current_index]:
                graph.connect(current_index, previous_index)
        # Set group for next lines.
        for _ in range(1, way.get_height()):
            # Set group for first column.
            way.increment()
            current_index = way.to_index(way.current())
            above_index = way.to_index(way.above())
            if data[current_index] == data[above_index]:
                graph.connect(current_index, above_index)
            # Set group for next columns.
            for _ in range(1, way.get_width()):
                way.increment()
                current_index = way.to_index(way.current())
                above_index = way.to_index(way.above())
                if data[current_index] == data[above_index]:
                    graph.connect(current_index, above_index)
        assert way.current() == way.last(), (way.current(), way.last())

    # Get groups
    final_groups = []
    while graph.edges:
        index = next(iter(graph.edges))
        group = {index}
        other_indices = graph.edges.pop(index)
        while other_indices:
            other_index = other_indices.pop()
            if other_index not in group:
                group.add(other_index)
                other_indices.update(graph.edges.pop(other_index))
        identifiers = set(data[i] for i in group)
        assert len(identifiers) == 1, len(identifiers)
        final_groups.append(group)

    # Display number of groups.
    print('Number of pixels:', width * height, len(set(data)))
    print('Number of groups:', len(final_groups))

    color_iterator = ColorIterator(2 ** 6)
    group_to_color = [color_iterator.next() for _ in range(len(final_groups))]
    position_to_color = [(0, 0, 0)] * width * height
    for group_id, group in enumerate(final_groups):
        color = group_to_color[group_id]
        for identifier in group:
            position_to_color[identifier] = color
    return position_to_color


def main():
    api = API(TEST_LIST_FILE_PATH, update=False)
    videos = sorted(api.database.readable.found.with_thumbnails)  # type: List[Video]
    video = videos[3]
    thumbnail_path = video.thumbnail_path
    img = Image.open(thumbnail_path.path)
    # Categorize pixels.
    output_data = [categorize_pixel(pixel) for pixel in img.getdata()]

    Display.from_images(
        img,
        new_rgb_image(output_data, *img.size),
        new_rgb_image(segment_image_1(output_data, *img.size), *img.size),
        new_rgb_image(segment_image_2(output_data, *img.size), *img.size),
        new_rgb_image(segment_image_3(output_data, *img.size), *img.size),
    )

    # miniatures = api.database.ensure_miniatures(return_miniatures=True)
    # min_dict = {m.identifier: m for m in miniatures}
    # miniature = min_dict[video.filename.path]
    # image = new_rgb_image(miniature.data(), miniature.width, miniature.height)
    # Display.from_images(image)


class Test:

    @staticmethod
    def test_points():
        for k, l in POINTS.items():
            c = k ** 3
            points = [i * (l + 1) for i in range(k)]
            print(f"k = {k}; c = {c}; l = {l}", points)

    @staticmethod
    def test_ways():
        arr = []
        w = 3
        h = 2
        for y in range(h):
            for x in range(w):
                arr.append((y, x))

        for way in (WayRightBottom(w, h), WayLeftTop(w, h), WayBottomRight(w, h), WayTopLeft(w, h)):
            print(type(way).__name__, (w, h))
            for _ in range(way.get_height()):
                for _ in range(way.get_width()):
                    print(way.current(), end=' ')
                    way.increment()
                print()
            print()

    @staticmethod
    def test_color_iterator():
        colors = []
        color_iterator = ColorIterator(2 ** 4)
        while not color_iterator.is_white():
            colors.append(color_iterator.next())
        for i, color in enumerate(colors):
            print(i + 1, color)


if __name__ == '__main__':
    # Test.test_color_iterator()
    main()
