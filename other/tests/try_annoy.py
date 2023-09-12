"""
Distance angular: 1.4142135381698608
Distance euclidean: 14133.435546875
sqrt 55.42523743872549 sqrt^2 3071.9569451390976
Distance manhattan: 783360.0
Distance hamming: 3072.0
Distance dot: 0.0
Expected euclidian 14133.534589762037 55.42562584220407
Expected manhattan 783360
"""
import json
import math
import sys
from typing import Iterator

from annoy import AnnoyIndex
from tqdm import tqdm, trange

from other.tests.utils_testing import DB_NAME
from pysaurus.core.functions import coord_to_flat, flat_to_coord
from pysaurus.core.modules import ImageUtils
from pysaurus.core.notifying import DEFAULT_NOTIFIER
from pysaurus.core.profiling import Profiler
from pysaurus.database.db_way_def import DbWays
from pysaurus.database.thubmnail_database.thumbnail_manager import ThumbnailManager
from saurus.sql.pysaurus_program import PysaurusProgram


def warn(notification):
    return print(notification, file=sys.stderr)


DEFAULT_NOTIFIER.set_default_manager(warn)


def get_around(i: int, w: int, h: int) -> Iterator[int]:
    x, y = flat_to_coord(i, w)
    for rx in range(max(0, x - 1), min(x + 2, w)):
        for ry in range(max(0, y - 1), min(y + 2, h)):
            yield coord_to_flat(rx, ry, w)


def merge_around(data, width, height, index):
    around = list(get_around(index, width, height))
    return (
        round(sum(data[pos][0] for pos in around) / len(around)),
        round(sum(data[pos][1] for pos in around) / len(around)),
        round(sum(data[pos][2] for pos in around) / len(around)),
    )


W, H = ImageUtils.DEFAULT_THUMBNAIL_SIZE

def main():
    metric = "euclidean"
    application = PysaurusProgram()
    db_name_to_path = {path.title: path for path in application.get_database_paths()}
    assert DB_NAME in db_name_to_path, (DB_NAME, db_name_to_path.keys())
    db_path = db_name_to_path[DB_NAME]
    ways = DbWays(db_path)
    thumb_sql_path = ways.db_thumb_sql_path
    assert thumb_sql_path.isfile()
    thumb_manager = ThumbnailManager(thumb_sql_path)
    nb_images = thumb_manager.thumb_db.query_one(
        "SELECT COUNT(filename) FROM video_to_thumbnail"
    )[0]
    vectors = []
    with tqdm(total=nb_images, desc="get vectors") as bar:
        for i, row in enumerate(
            thumb_manager.thumb_db.query(
                "SELECT filename, thumbnail FROM video_to_thumbnail"
            )
        ):
            image = ImageUtils.from_blob(row["thumbnail"])
            thumbnail = image.resize(ImageUtils.DEFAULT_THUMBNAIL_SIZE)
            data = list(thumbnail.getdata())
            vector = [v for index in range(len(data)) for v in merge_around(data, W, H, index)]
            vectors.append((row["filename"], vector))
            bar.update(1)

    vector_size = 3 * 1024
    with Profiler("Check vectors"):
        assert all(len(vector[1]) == vector_size for vector in vectors)
    with Profiler("Build Annoy index"):
        t = AnnoyIndex(vector_size, metric)
        for i, (filename, vector) in tqdm(
            list(enumerate(vectors)), desc="Add items to Annoy"
        ):
            t.add_item(i, vector)

        with Profiler("Build Annoy trees"):
            t.build(100)
        with Profiler("Save Annoy to disk"):
            t.save("ignored/test.ann")
    results = [
        (i, t.get_nns_by_item(i, 4, include_distances=True))
        for i in trange(len(vectors), desc="Search in Annoy index")
    ]
    output = {
        vectors[i][0]: [[dst, vectors[j][0]] for j, dst in zip(ids, dsts)]
        for i, (ids, dsts) in results
    }
    with open(f"ignored/results_{metric}.json", "w") as file:
        json.dump(output, file, indent=1)


def main_2():
    vector_size = 3 * 1024
    # add black and white thumbnails
    for metric in ("angular", "euclidean", "manhattan", "hamming", "dot"):
        vector_black = [0] * vector_size
        vector_white = [255] * vector_size
        i_black = 0
        i_white = 1
        t = AnnoyIndex(vector_size, metric)
        t.add_item(i_black, vector_black)
        t.add_item(i_white, vector_white)
        t.build(10)
        dst = t.get_distance(i_black, i_white)
        print(f"Distance {metric}:", dst)
        if metric == "euclidean":
            print("sqrt", dst / 255, "sqrt^2", (dst / 255) ** 2)

    print("Expected euclidian", 255 * math.sqrt(vector_size), math.sqrt(vector_size))
    print("Expected manhattan", 255 * vector_size)


if __name__ == "__main__":
    main()
