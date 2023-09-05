import json
import os.path
from collections import Counter
from io import BytesIO
from typing import List, Tuple

import imagehash
from PIL import Image
from tqdm import tqdm

from pysaurus.core.functions import coord_to_flat, flat_to_coord
from pysaurus.core.modules import ImageUtils
from pysaurus.database.db_way_def import DbWays
from pysaurus.database.thubmnail_database.thumbnail_manager import ThumbnailManager
from saurus.sql.pysaurus_program import PysaurusProgram
from .utils_testing import DB_NAME


def blob_to_image(binary_data) -> Image:
    blob = BytesIO(binary_data)
    return ImageUtils.open_rgb_image(blob)


W = ImageUtils.DEFAULT_THUMBNAIL_DIMENSION


def hash_image(thumbnail: Image):
    return sum(
        (sum(px) + 1) * ((i % W) + 1) * ((i // W) + 1)
        for i, px in enumerate(thumbnail.getdata())
    )


def get_near_zones(width: int, height: int) -> List[List[int]]:
    zones = [None] * (width * height)
    zones[coord_to_flat(0, 0, width)] = [
        coord_to_flat(0, 0, width),
        coord_to_flat(1, 0, width),
        coord_to_flat(0, 1, width),
        coord_to_flat(1, 1, width),
    ]
    zones[coord_to_flat(width - 1, 0, width)] = [
        coord_to_flat(width - 2, 0, width),
        coord_to_flat(width - 1, 0, width),
        coord_to_flat(width - 2, 1, width),
        coord_to_flat(width - 1, 1, width),
    ]
    zones[coord_to_flat(0, height - 1, width)] = [
        coord_to_flat(0, height - 1, width),
        coord_to_flat(1, height - 1, width),
        coord_to_flat(0, height - 2, width),
        coord_to_flat(1, height - 2, width),
    ]
    zones[coord_to_flat(width - 1, height - 1, width)] = [
        coord_to_flat(width - 2, height - 1, width),
        coord_to_flat(width - 1, height - 1, width),
        coord_to_flat(width - 2, height - 2, width),
        coord_to_flat(width - 1, height - 2, width),
    ]
    for x in range(1, width - 1):
        zones[coord_to_flat(x, 0, width)] = [
            coord_to_flat(x - 1, 0, width),
            coord_to_flat(x, 0, width),
            coord_to_flat(x + 1, 0, width),
            coord_to_flat(x - 1, 1, width),
            coord_to_flat(x, 1, width),
            coord_to_flat(x + 1, 1, width),
        ]
        zones[coord_to_flat(x, height - 1, width)] = [
            coord_to_flat(x - 1, height - 1, width),
            coord_to_flat(x, height - 1, width),
            coord_to_flat(x + 1, height - 1, width),
            coord_to_flat(x - 1, height - 2, width),
            coord_to_flat(x, height - 2, width),
            coord_to_flat(x + 1, height - 2, width),
        ]
    for y in range(1, height - 1):
        zones[coord_to_flat(0, y, width)] = [
            coord_to_flat(0, y - 1, width),
            coord_to_flat(1, y - 1, width),
            coord_to_flat(0, y, width),
            coord_to_flat(1, y, width),
            coord_to_flat(0, y + 1, width),
            coord_to_flat(1, y + 1, width),
        ]
        zones[coord_to_flat(width - 1, y, width)] = [
            coord_to_flat(width - 2, y - 1, width),
            coord_to_flat(width - 1, y - 1, width),
            coord_to_flat(width - 2, y, width),
            coord_to_flat(width - 1, y, width),
            coord_to_flat(width - 2, y + 1, width),
            coord_to_flat(width - 1, y + 1, width),
        ]
    for x in range(1, width - 1):
        for y in range(1, height - 1):
            zones[coord_to_flat(x, y, width)] = [
                coord_to_flat(x - 1, y - 1, width),
                coord_to_flat(x, y - 1, width),
                coord_to_flat(x + 1, y - 1, width),
                coord_to_flat(x - 1, y, width),
                coord_to_flat(x, y, width),
                coord_to_flat(x + 1, y, width),
                coord_to_flat(x - 1, y + 1, width),
                coord_to_flat(x, y + 1, width),
                coord_to_flat(x + 1, y + 1, width),
            ]
    return zones


class PixelClassifier:
    # [1, 3, 5, 15, 17, 51, 85, 255]
    INTERVAL_LENGTHS = [v for v in range(1, 256) if not 255 % v]
    # [256, 86, 52, 18, 16, 6, 4, 2]
    UNIT_CLASSES = [(255 // v) + 1 for v in INTERVAL_LENGTHS]
    # pixel classes:
    # [16777216, 636056, 140608, 5832, 4096, 216, 64, 8]

    __slots__ = ("nb_classes", "interval_length", "min_pop")

    def __init__(self, interval_length=None, nb_classes=4, min_pop=2):
        if interval_length is not None:
            assert nb_classes is None
            assert interval_length in self.INTERVAL_LENGTHS
            nb_classes = (255 // interval_length) + 1
            assert nb_classes in self.UNIT_CLASSES
        else:
            assert nb_classes is not None
            assert nb_classes in self.UNIT_CLASSES
            interval_length = 255 // (nb_classes - 1)
            assert interval_length in self.INTERVAL_LENGTHS
        self.nb_classes = nb_classes
        self.interval_length = interval_length
        self.min_pop = min_pop

    def classify(self, pixel: Tuple[int, int, int]) -> Tuple:
        return tuple(
            int(v // self.interval_length) * self.interval_length for v in pixel
        )

    def get_pixel_populations(self, thumbnail: Image):
        counter = Counter(self.classify(px) for px in thumbnail.getdata())
        return sorted(
            color[0] * 1_000_000 + color[1] * 1_000 + color[2]
            for color, count in counter.items()
            if count >= self.min_pop
        )


class NearPixelHash:
    def __init__(self, width, height, classifier: PixelClassifier):
        self.classifier = classifier
        self.width = width
        self.height = height
        self.zones = get_near_zones(width, height)

    def hash(self, thumbnail: Image):
        data = list(thumbnail.getdata())
        return tuple(
            self.classifier.classify(
                (
                    sum(data[j][0] for j in self.zones[i]) / len(self.zones[i]),
                    sum(data[j][1] for j in self.zones[i]) / len(self.zones[i]),
                    sum(data[j][2] for j in self.zones[i]) / len(self.zones[i]),
                )
            )
            for i in range(len(data))
        )


OUTPUT_PATH = "ignored/hash.json"


def main_0():
    interval_lengths = [v for v in range(1, 256) if not 255 % v]
    print(len(interval_lengths), interval_lengths)
    for interval_length in interval_lengths:
        expected_nb_classes = 256 // interval_length + bool(256 % interval_length)
        classes = sorted(
            {int(v // interval_length) * interval_length for v in range(256)}
        )
        print(
            "Interval",
            interval_length,
            "classes",
            expected_nb_classes,
            "colors",
            len(classes) ** 3,
        )
        assert expected_nb_classes == len(classes)
        nb_cls = len(classes)
        if nb_cls != 1:
            assert ((256 - nb_cls) / (nb_cls - 1)) + 1 == interval_length
        assert nb_cls == (255 // interval_length) + 1


def main_1():
    application = PysaurusProgram()
    db_name_to_path = {path.title: path for path in application.get_database_paths()}

    classifier = PixelClassifier()
    output_path = "../../pysaurus/updates/ignored/hash.json"
    if True or not os.path.isfile(output_path):
        assert DB_NAME in db_name_to_path
        db_path = db_name_to_path[DB_NAME]
        ways = DbWays(db_path)
        thumb_sql_path = ways.db_thumb_sql_path
        assert thumb_sql_path.isfile()
        thumb_manager = ThumbnailManager(thumb_sql_path)
        nb_images = thumb_manager.thumb_db.query_one(
            "SELECT COUNT(filename) FROM video_to_thumbnail"
        )[0]
        computation = []
        with tqdm(total=nb_images) as bar:
            for i, row in enumerate(
                thumb_manager.thumb_db.query(
                    "SELECT filename, thumbnail FROM video_to_thumbnail"
                )
            ):
                image = blob_to_image(row["thumbnail"])
                thumbnail = image.resize(ImageUtils.DEFAULT_THUMBNAIL_SIZE)
                computation.append(
                    [
                        hash_image(thumbnail),
                        str(classifier.get_pixel_populations(thumbnail)),
                        row["filename"],
                    ]
                )
                bar.update(1)
        computation.sort(key=lambda c: (c[0], c[2]))
        with open(output_path, "w") as file:
            json.dump(computation, file, indent=1)

        # Try to find similarities.
        similarities = {}
        for hash_val, pop_val, filename in computation:
            similarities.setdefault(pop_val, []).append((hash_val, filename))
        for pop_val, candidates in similarities.items():
            if len(candidates) > 1:
                print(pop_val)
                for h, f in candidates:
                    print("\t", h, f)


def main_1_1():
    application = PysaurusProgram()
    db_name_to_path = {path.title: path for path in application.get_database_paths()}

    classifier = PixelClassifier()
    near_hasher = NearPixelHash(W, W, classifier)
    output_path = "../../pysaurus/updates/ignored/hash.json"
    if True or not os.path.isfile(output_path):
        assert DB_NAME in db_name_to_path
        db_path = db_name_to_path[DB_NAME]
        ways = DbWays(db_path)
        thumb_sql_path = ways.db_thumb_sql_path
        assert thumb_sql_path.isfile()
        thumb_manager = ThumbnailManager(thumb_sql_path)
        nb_images = thumb_manager.thumb_db.query_one(
            "SELECT COUNT(filename) FROM video_to_thumbnail"
        )[0]
        computation = []
        with tqdm(total=nb_images) as bar:
            for i, row in enumerate(
                thumb_manager.thumb_db.query(
                    "SELECT filename, thumbnail FROM video_to_thumbnail"
                )
            ):
                image = blob_to_image(row["thumbnail"])
                thumbnail = image.resize(ImageUtils.DEFAULT_THUMBNAIL_SIZE)
                computation.append([near_hasher.hash(thumbnail), row["filename"]])
                bar.update(1)

        # computation.sort(key=lambda c: (c[0], c[2]))
        # with open(output_path, "w") as file:
        #     json.dump(computation, file, indent=1)

        # Try to find similarities.
        similarities = {}
        for hash_val, filename in computation:
            if (
                "lorena_sanchez_niceroundass" in filename
                or "lorena-sanchez-loves-hard-cock - p1080" in filename
            ):
                print(filename)
                print("\t", hash_val)
            similarities.setdefault(hash_val, []).append(filename)
        for hash_val, candidates in similarities.items():
            if len(candidates) > 1:
                print("SIM")
                for f in candidates:
                    print("\t", f)


def main_2():
    application = PysaurusProgram()
    db_name_to_path = {path.title: path for path in application.get_database_paths()}
    assert DB_NAME in db_name_to_path
    db_path = db_name_to_path[DB_NAME]
    ways = DbWays(db_path)
    thumb_sql_path = ways.db_thumb_sql_path
    assert thumb_sql_path.isfile()
    thumb_manager = ThumbnailManager(thumb_sql_path)
    nb_images = thumb_manager.thumb_db.query_one(
        "SELECT COUNT(filename) FROM video_to_thumbnail"
    )[0]
    computation = []
    with tqdm(total=nb_images) as bar:
        for i, row in enumerate(
            thumb_manager.thumb_db.query(
                "SELECT filename, thumbnail FROM video_to_thumbnail"
            )
        ):
            image = blob_to_image(row["thumbnail"])
            ah = imagehash.average_hash(image, hash_size=8)
            computation.append([ah, row["filename"]])
            bar.update(1)

    # Try to find similarities.
    similarities = {}
    for hash_val, filename in computation:
        similarities.setdefault(hash_val, []).append(filename)
    for hash_val, candidates in similarities.items():
        if len(candidates) > 1:
            print(hash_val)
            for f in candidates:
                print("\t", f)

    # with open(OUTPUT_PATH, "w") as file:
    #     json.dump(similarities, file, indent=1)


def main_3():
    zones = get_near_zones(W, W)
    for i, near in enumerate(zones):
        print(flat_to_coord(i, W), [flat_to_coord(j, W) for j in near])


if __name__ == "__main__":
    main_1_1()
