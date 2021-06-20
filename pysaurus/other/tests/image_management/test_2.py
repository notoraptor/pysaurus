from collections import Counter
from typing import Dict, Tuple, List, Union

from pysaurus.other.tests.image_management.test_utils import Tester

from pysaurus.core import functions
from pysaurus.core.classes import StringPrinter
from pysaurus.core.miniature import Miniature
from pysaurus.other.tests.image_management.elements.basic_group import BasicGroup
from pysaurus.other.tests.image_management.elements.draw import (
    Draw,
    dilate_miniature_data,
)
from pysaurus.other.tests.image_management.elements.group_computer import GroupComputer
from pysaurus.other.tests.image_management.elements.pixel_group import PixelGroup


class PixelMapper:
    @staticmethod
    def map_interval(pixel: Tuple[int, int, int], interval_length: int) -> Tuple:
        return tuple(int(v // interval_length) * interval_length for v in pixel)


class ProcessedImage:
    __slots__ = (
        "name",
        "data",
        "width",
        "height",
        "color_count",
        "color_center",
        "bg_to_pg",
    )

    def __init__(
        self, name, data, width, height, bg_to_pg: Dict[BasicGroup, PixelGroup]
    ):
        color_indices = {}
        for index, color in enumerate(data):
            color_indices.setdefault(color, []).append(index)

        self.name = name
        self.data = data
        self.width = width
        self.height = height
        self.color_count = Counter(self.data)
        self.color_center = {
            color: tuple(v for v in self.get_center(color_indices[color], self.width))
            for color in color_indices
        }
        self.bg_to_pg = bg_to_pg

    def __str__(self):
        with StringPrinter() as printer:
            printer.write(
                self.name,
                len(self.color_center),
                f"color{'s' if len(self.color_center) > 1 else ''}",
            )
            for i, color in enumerate(sorted(self.color_center)):
                printer.write(
                    f"\t[{i + 1}] {color} count {self.color_count[color]} center {self.color_center[color]}"
                )
            return str(printer)

    def get_color_prop_c(self, color):
        return self.color_count.get(color, 0)

    def get_color_prop_x(self, color):
        return self.color_center.get(color, (-1, -1))[0]

    def get_color_prop_y(self, color):
        return self.color_center.get(color, (-1, -1))[1]

    def get(self, axe_key):
        color, prop = axe_key
        return getattr(self, f"get_color_prop_{prop}")(color)

    def get_group_prop(self, axe_key):
        basic_group, prop = axe_key
        pixel_groups = self.bg_to_pg.get(basic_group, ())
        if prop == Space.C:
            if group in self.groups:
                return group.size
            return 0
        if prop == Space.X:
            if group in self.groups:
                return group.center[0]
            return -1
        if prop == Space.Y:
            if group in self.groups:
                return group.center[1]
            return -1
        raise ValueError(f"Unknown prop {prop}")

    @staticmethod
    def get_center(indices: List[int], width: int):
        nb_points = len(indices)
        total_x = 0
        total_y = 0
        for index in indices:
            x, y = functions.flat_to_coord(index, width)
            total_x += x
            total_y += y
        return total_x / nb_points, total_y / nb_points


class Space:
    C = "c"
    X = "x"
    Y = "y"
    LIMITS = {"c": 64, "x": 8, "y": 8}

    @staticmethod
    def get_axe_key(color, prop):
        return color, prop

    @staticmethod
    def get_group_key(group, prop):
        return group, prop

    @staticmethod
    def segment(
        images: List[ProcessedImage],
        axe_key: Tuple[Tuple[int, int, int], str],
        limit: Union[int, float],
    ) -> List[List[ProcessedImage]]:
        output = []
        value_to_images = {}
        for image in images:
            value_to_images.setdefault(image.get(axe_key), []).append(image)
        excluded_images = value_to_images.pop(-1, [])
        values = sorted(value_to_images.keys())
        cursor = 0
        for i in range(1, len(values)):
            if values[i] - values[i - 1] > limit:
                cluster = []
                for j in range(cursor, i):
                    cluster.extend(value_to_images[values[j]])
                output.append(cluster)
                print(
                    f'\t{axe_key} split {values[i - 1]} {values[i]} ({", ".join(img.name for img in cluster)}) vs ({", ".join(img.name for img in images if img not in cluster)})'
                )
                cursor = i
        cluster = []
        for j in range(cursor, len(values)):
            cluster.extend(value_to_images[values[j]])
        output.append(cluster)
        if excluded_images:
            for cluster in output:
                cluster.extend(excluded_images)
        return [cluster for cluster in output if len(cluster) > 1]

    @staticmethod
    def segment_by_group(
        images: List[ProcessedImage],
        axe_key: Tuple[BasicGroup, str],
        limit: Union[int, float],
    ) -> List[List[ProcessedImage]]:
        output = []
        value_to_images = {}
        for image in images:
            value_to_images.setdefault(image.get_group_prop(axe_key), []).append(image)
        excluded_images = value_to_images.pop(-1, [])
        values = sorted(value_to_images.keys())
        cursor = 0
        for i in range(1, len(values)):
            if values[i] - values[i - 1] > limit:
                cluster = []
                for j in range(cursor, i):
                    cluster.extend(value_to_images[values[j]])
                output.append(cluster)
                print(
                    f'\t{axe_key} split {values[i - 1]} {values[i]} ({", ".join(img.name for img in cluster)}) vs ({", ".join(img.name for img in images if img not in cluster)})'
                )
                cursor = i
        cluster = []
        for j in range(cursor, len(values)):
            cluster.extend(value_to_images[values[j]])
        output.append(cluster)
        if excluded_images:
            for cluster in output:
                cluster.extend(excluded_images)
        return [cluster for cluster in output if len(cluster) > 1]

    def __init__(self, processed_images: List[ProcessedImage]):
        colors = set()
        groups = set()
        for image in processed_images:
            colors.update(image.color_center.keys())
            groups.update(image.groups)
        self.images = processed_images
        self.colors = sorted(colors)
        self.groups = sorted(groups)
        print(len(self.colors), "color(s)")
        print(len(self.groups), "group(s)")

    def categorize(self):
        segments = [self.images]  # type: List[List[ProcessedImage]]
        for prop in (self.C, self.X, self.Y):
            for color in self.colors:
                axe_key = self.get_axe_key(color, prop)
                new_segments = []
                for segment in segments:
                    clusters = self.segment(segment, axe_key, self.LIMITS[prop])
                    new_segments.extend(clusters)
                self.debug(new_segments)
                print(
                    "Segment",
                    axe_key,
                    "before",
                    len(segments),
                    "after",
                    len(new_segments),
                    "total",
                    sum(len(s) for s in new_segments),
                )
                segments = new_segments
        return segments

    def categorize_by_group(self):
        segments = [self.images]  # type: List[List[ProcessedImage]]
        for prop in (self.C, self.X, self.Y):
            for group in self.groups:
                axe_key = self.get_group_key(group, prop)
                new_segments = []
                for segment in segments:
                    clusters = self.segment_by_group(
                        segment, axe_key, self.LIMITS[prop]
                    )
                    new_segments.extend(clusters)
                self.debug(new_segments)
                print(
                    "Segment",
                    axe_key,
                    "before",
                    len(segments),
                    "after",
                    len(new_segments),
                    "total",
                    sum(len(s) for s in new_segments),
                )
                segments = new_segments
        return segments

    def debug(self, segments: List[List[ProcessedImage]]):
        similarities = (
            ("a1", "a2", "a3"),
            ("b1", "b2", "b3"),
            ("c1", "c2", "c3"),
            ("d1", "d2", "d3", "d4"),
        )
        for i, segment in enumerate(segments):
            names = {image.name for image in segment}
            for similarity in similarities:
                if any(name in names for name in similarity) and not all(
                    name in names for name in similarity
                ):
                    missing = [name for name in similarity if name not in names]
                    print(
                        f"Similarity [{i + 1}/{len(similarities)}] {similarity} is missing {missing}"
                    )
                    exit(-1)


class Run(Tester):
    __slots__ = (
        "mapped_files",
        "nb_color_points",
        "nb_position_points",
        "nb_size_points",
        "pixel_distance_radius",
        "group_min_size",
    )

    def __init__(self, files=None):
        if files:
            super().__init__(video_filenames=[t[1] for t in files])
            self.mapped_files = files
        else:
            super().__init__()
        self.nb_color_points = 8
        self.nb_position_points = 4
        self.nb_size_points = 4
        self.pixel_distance_radius = 6
        self.group_min_size = 1

    def miniature_to_groups(self, group_computer: GroupComputer, miniature: Miniature):
        bg_to_pg = {}
        for pg in group_computer.compute_groups(miniature):
            bg = pg.to_basic_group_intervals_alt(
                self.nb_color_points, self.nb_position_points, self.nb_size_points
            )
            bg_to_pg.setdefault(bg, []).append(pg)
        return bg_to_pg

    def run(self):
        print(len(self.miniatures), "Miniatures")
        similarity_percent = (255 - self.pixel_distance_radius) * 100 / 255
        group_computer = GroupComputer(
            group_min_size=self.group_min_size, similarity_percent=similarity_percent
        )
        img_to_pixel_groups = []
        img_to_basic_groups = []
        all_basic_groups = set()
        for m in self.miniatures:
            pixel_groups = group_computer.compute_groups(m)
            basic_groups = [
                pg.to_basic_group_intervals_alt(
                    self.nb_color_points, self.nb_position_points, self.nb_size_points
                )
                for pg in pixel_groups
            ]
            img_to_pixel_groups.append(pixel_groups)
            img_to_basic_groups.append(basic_groups)
            all_basic_groups.update(basic_groups)
        print(len(all_basic_groups), "basic group(s)")

        mapped_miniatures = []
        for i, miniature in enumerate(self.miniatures):
            output = [
                PixelMapper.map_interval(pixel, 256 // 8)
                for pixel in list(miniature.data())
            ]
            mapped_miniatures.append(
                ProcessedImage(
                    self.mapped_files[i][0],
                    output,
                    miniature.width,
                    miniature.height,
                    self.miniature_to_groups(group_computer, miniature),
                )
            )
        space = Space(mapped_miniatures)
        space.categorize_by_group()
        dec = 4
        surface = Draw(
            128 * len(self.miniatures) + dec * (len(self.miniatures) - 1), 128 * 2 + dec
        )
        for i in range(len(self.miniatures)):
            m = self.miniatures[i]
            s = mapped_miniatures[i]
            # print(s)
            m_data = dilate_miniature_data(list(m.data()), m.width, m.height)
            s_data = dilate_miniature_data(s.data, m.width, m.height)
            surface.draw_data(m_data, 128, 128, i * (128 + dec), 0)
            surface.draw_data(s_data, 128, 128, i * (128 + dec), 128 + dec)
        # surface.display()


def main():
    _files = [
        (
            "a1",
            r"J:\donnees\divers\autres\p\[HD, 1920x1080p] Fucked and Oiled Up - Susy Gala  HD-Porn.me.mp4",
        ),
        (
            "a2",
            r"Q:\donnees\autres\p\Susy Gala - Fucked And Oiled Up - Ready Or Not Here I Cum #bigtits.mp4",
        ),
        (
            "a3",
            r"Q:\donnees\autres\p\Susy Gala - Nacho's First Class Fucks (2016) #POV.mp4",
        ),
        (
            "b1",
            r"J:\donnees\divers\autres\p\Hannah Hays - Biggest Black Cock - XFREEHD.mp4",
        ),
        ("b2", r"M:\donnees\autres\p\Hannah Hays - Interracial Pickups.mp4"),
        ("b3", r"Q:\donnees\autres\p\Hannah Hays_2.mp4"),
        (
            "c1",
            r"J:\donnees\divers\autres\p\Daya Knight - black teacher helping little boy study - 1080.mp4",
        ),
        ("c2", r"L:\donnees\autres\p\Daya Knight - bkb16158-1080p.mp4"),
        ("c3", r"M:\donnees\autres\p\daya knight - Young Guy Fucks Ebony Lady.mp4"),
        (
            "d1",
            r"E:\donnees\autres\p\busty-asian-real-estate-agent-gets-her-pussy-destroyed_1080p.mp4",
        ),
        ("d2", r"J:\donnees\divers\autres\p\Mena Li and a big black cock__p720.mp4"),
        (
            "d3",
            r"M:\donnees\autres\p\mena li - Asian pussy gets destroyed with a BBC__p720.mp4",
        ),
        (
            "d4",
            r"R:\donnees\autres\p\mena li - Scene 2 From Chocolate Desires - 1080p.mp4",
        ),
    ]
    Run(_files).run()


if __name__ == "__main__":
    main()
