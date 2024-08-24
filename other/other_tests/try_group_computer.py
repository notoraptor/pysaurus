import json
import os
import sys
from collections import Counter
from typing import List, Tuple

from tqdm import tqdm

from other.other_tests.try_finding_similarities import DB_NAME, W, blob_to_image
from pysaurus.core.classes import AbstractMatrix
from pysaurus.core.components import AbsolutePath, Date
from pysaurus.core.modules import ImageUtils
from pysaurus.core.profiling import Profiler
from pysaurus.database.db_settings import DbSettings
from pysaurus.database.db_way_def import DbWays
from pysaurus.database.jsdb.thubmnail_database import ThumbnailManager
from pysaurus.miniature.group_computer import GroupComputer
from pysaurus.miniature.pixel_group import PixelGroup
from saurus.sql.pysaurus_program import PysaurusProgram


class PysaurusImage(AbstractMatrix):
    __slots__ = ("image",)

    def __init__(self, *, path: AbsolutePath = None, image=None):
        assert (image is not None) ^ (path is not None)
        self.image = image or ImageUtils.open_rgb_image(path.path)
        super().__init__(*self.image.size)

    def data(self):
        return self.image.getdata()


class PixelGroupDescriptor:
    __slots__ = ("r", "g", "b", "x", "y", "w", "h", "n")
    RADIUS = 1
    R, G, B, X, Y, W, H, N = range(8)

    def __init__(
        self,
        color: Tuple[int, int, int],
        rect: Tuple[int, int, int, int],
        nb_pixels: int,
    ):
        self.r, self.g, self.b = color
        self.x, self.y, self.w, self.h = rect
        self.n = nb_pixels

    def __str__(self):
        return (
            f"{self.r}_{self.g}_{self.b}|{self.x}_{self.y}_{self.w}_{self.h}|{self.n}"
        )

    __repr__ = __str__

    def flatten(self):
        return [
            [self.R, self.r],
            [self.G, self.g],
            [self.B, self.b],
            [self.X, self.x],
            [self.Y, self.y],
            [self.W, self.w],
            [self.H, self.h],
            [self.N, self.n],
        ]

    def to_json(self):
        return [self.r, self.g, self.b, self.x, self.y, self.w, self.h, self.n]

    @classmethod
    def from_json(cls, flat):
        return cls(
            (flat[0], flat[1], flat[2]), (flat[3], flat[4], flat[5], flat[6]), flat[7]
        )

    def expand(self, width, height, min_size):
        for base, radius, key, a, b in (
            (self.r, self.RADIUS, self.R, 0, 256),
            (self.g, self.RADIUS, self.G, 0, 256),
            (self.b, self.RADIUS, self.B, 0, 256),
            (self.x, self.RADIUS, self.X, 0, width),
            (self.y, self.RADIUS, self.Y, 0, height),
            (self.w, self.RADIUS, self.W, 1, width + 1),
            (self.h, self.RADIUS, self.H, 1, height + 1),
            (self.n, self.RADIUS, self.N, min_size, width * height + 1),
        ):
            for val in range(max(a, base - radius), min(b, base + radius + 1)):
                yield (key, val)


def main():
    path3 = AbsolutePath(
        r"C:\Users\notoraptor-desktop\Pictures\vlcsnap-2023-08-09-12h26m54s833.png"
    )
    path = path3
    settings = DbSettings()
    # pixel_distance_radius = 6
    # normalizer = 0
    # for pixel_distance_radius in (6, 5, 4, 3, 2):
    # for normalizer in (0, 1, 2, 3):
    for pixel_distance_radius in (2,):
        for normalizer in (1,):
            group_computer = GroupComputer(
                group_min_size=settings.miniature_group_min_size,
                pixel_distance_radius=pixel_distance_radius,
                normalizer=normalizer,
            )
            image = PysaurusImage(path=path)
            # d1 = group_computer.pixel_comparator._normalize_data_1(image.data(), image.width)
            # d2 = group_computer.pixel_comparator._normalize_data_2(image.data(), image.width)
            # o1 = ImageUtils.new_rgb_image(d1, image.width, image.height)
            # o2 = ImageUtils.new_rgb_image(d2, image.width, image.height)
            # Display.from_images(image.image.resize((300, 300)), o1.resize((300, 300)), o2.resize((300, 300)))
            # return

            with Profiler("group pixels"):
                groups = group_computer.group_pixels(image)
            output = [(0, 0, 0)] * (image.width * image.height)
            descriptors = []
            # r, g, b, x, y, w, h, n
            with Profiler("generate output"):
                for group in groups:
                    color = tuple(int(v) for v in group.color)
                    descriptors.append(
                        PixelGroupDescriptor(color, group.rect, len(group.members))
                    )
                    for index in group.members:
                        output[index] = color
            with Profiler("generate new image"):
                new_image = ImageUtils.new_rgb_image(output, image.width, image.height)

            new_image.save(
                f"ignored/r{pixel_distance_radius}_n{normalizer}_t{Date.now().time}.jpg"
            )

            for i, k in enumerate(
                descriptors[0].expand(
                    image.width, image.height, group_computer.group_min_size
                )
            ):
                print(i, k)
            # Display.from_images(new_image)


def essay():
    group_min_size = 2
    pixel_distance_radius = 4
    normalizer = 0
    output_path = (
        f"ignored/"
        f"usable_computation_g{group_min_size}"
        f"_r{pixel_distance_radius}"
        f"_n{normalizer}.json"
    )
    print(
        f"Params: g={group_min_size} r={pixel_distance_radius} n={normalizer}",
        file=sys.stderr,
    )
    group_computer = GroupComputer(
        group_min_size=group_min_size,
        pixel_distance_radius=pixel_distance_radius,
        normalizer=normalizer,
    )

    application = PysaurusProgram()
    db_name_to_path = {path.title: path for path in application.get_database_paths()}
    db_path = db_name_to_path[DB_NAME]
    ways = DbWays(db_path)
    thumb_sql_path = ways.db_thumb_sql_path
    assert thumb_sql_path.isfile()
    thumb_manager = ThumbnailManager(thumb_sql_path)
    nb_images = thumb_manager.thumb_db.query_one(
        "SELECT COUNT(filename) FROM video_to_thumbnail"
    )[0]
    computation: List[Tuple[str, List[PixelGroup]]] = []
    usable_computation: List[Tuple[str, List[PixelGroupDescriptor]]]

    if os.path.isfile(output_path):

        with Profiler("load_usable_computation"):
            with open(output_path) as file:
                usable_computation = [
                    (
                        filename,
                        [
                            PixelGroupDescriptor.from_json(flat_desc)
                            for flat_desc in flat_descriptors
                        ],
                    )
                    for filename, flat_descriptors in json.load(file)
                ]

    else:

        with tqdm(total=nb_images, desc="segmentation") as bar:
            for row in thumb_manager.thumb_db.query(
                "SELECT filename, thumbnail FROM video_to_thumbnail"
            ):
                image = blob_to_image(row["thumbnail"])
                thumbnail = image.resize(ImageUtils.THUMBNAIL_SIZE)
                computation.append(
                    (
                        row["filename"],
                        group_computer.group_pixels(PysaurusImage(image=thumbnail)),
                    )
                )
                bar.update(1)

        with Profiler("usable_computation"):
            usable_computation: List[Tuple[str, List[PixelGroupDescriptor]]] = [
                (
                    filename,
                    [
                        PixelGroupDescriptor(
                            (
                                int(group.color[0]),
                                int(group.color[1]),
                                int(group.color[2]),
                            ),
                            group.rect,
                            len(group.members),
                        )
                        for group in groups
                    ],
                )
                for filename, groups in computation
            ]

        with Profiler("save_usable_computation"):
            with open(output_path, "w") as file:
                json.dump(
                    [
                        [filename, [desc.to_json() for desc in descriptors]]
                        for filename, descriptors in usable_computation
                    ],
                    file,
                )

    big_hasher = {}
    with tqdm(total=len(usable_computation), desc="great hashing") as bar:
        for filename, descriptors in usable_computation:
            # if (
            #     "lorena_sanchez_niceroundass" in filename
            #     or "lorena-sanchez-loves-hard-cock - p1080" in filename
            # ):
            #     print(filename, f"{len(descriptors)}")
            #     i = 0
            #     for desc in sorted(
            #         descriptors, key=lambda d: (-d.n, d.r, d.g, d.b, d.x, d.y, d.w, d.h)
            #     ):
            #         if desc.n > 2:
            #             print(f"\t({i + 1})", desc)
            #             i += 1
            # continue
            for pgd in descriptors:
                for key in pgd.expand(W, W, group_computer.group_min_size):
                    big_hasher.setdefault(key, []).append(filename)
            bar.update(1)

    # return

    # with Profiler("Hasher to sets"):
    #     usable_hasher = {key: set(values) for key, values in big_hasher.items()}
    # empty_set = set()

    with Profiler("File keys"):
        usable_keys = [
            (filename, [tuple(key) for desc in descriptors for key in desc.flatten()])
            for filename, descriptors in usable_computation
        ]

    found = []
    with tqdm(total=len(usable_keys), desc="find sim") as bar:
        for filename, keys in usable_keys:
            file_count = Counter()
            for key in keys:
                file_count.update(big_hasher.get(key, ()))
            filenames = [
                filename
                for filename, count in file_count.items()
                if count >= len(keys) * 90 / 100
            ]
            if len(filenames) > 1:
                found.append((filename, filenames))
            bar.update(1)

    for i, (filename, filenames) in enumerate(found):
        print(f"({i + 1})", filename)
        if filename in filenames:
            filenames.remove(filename)
        for similar in sorted(filenames):
            print("\t", similar)


if __name__ == "__main__":
    with Profiler("script"):
        essay()
