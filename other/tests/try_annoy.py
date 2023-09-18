"""
Distance angular: 1.4142135381698608
Distance euclidean: 14133.435546875
sqrt 55.42523743872549 sqrt^2 3071.9569451390976
Distance manhattan: 783360.0
Distance hamming: 3072.0
Distance dot: 0.0
Expected euclidian 14133.534589762037 55.42562584220407
Expected manhattan 783360
========================================================================================
ProfilingStart(main)
ProfilingStart(Get pre-computed similarities)
ProfilingEnded(Get pre-computed similarities, 552830µs)
Similarities 79
Similar videos 159
get vectors: 100%|██████████| 25247/25247 [00:20<00:00, 1209.56it/s]
check vectors: 100%|██████████| 25247/25247 [00:00<00:00, 2945825.61it/s]
Add items to Annoy: 100%|██████████| 25247/25247 [00:03<00:00, 8004.22it/s]
ProfilingStart(Build Annoy trees)
ProfilingEnded(Build Annoy trees, 09s 081409µs)
ProfilingStart(Save Annoy to disk)
ProfilingEnded(Save Annoy to disk, 414209µs)
Search in Annoy index: 100%|██████████| 25247/25247 [04:11<00:00, 100.20it/s]
Expected sims 159
Detected sims 435493
Truth rate 0.03651034574608547 %
ProfilingStart(Check expected similarities)
ProfilingEnded(Check expected similarities, 000133µs)
ProfilingEnded(main, 04m 48s 981723µs)
"""
import json
import math
import sys

from PIL import ImageFilter
from annoy import AnnoyIndex
from tqdm import tqdm, trange

from other.tests.utils_testing import DB_NAME
from pysaurus.core.components import AbsolutePath
from pysaurus.core.modules import ImageUtils
from pysaurus.core.profiling import Profiler
from pysaurus.database.db_way_def import DbWays
from pysaurus.database.thubmnail_database.thumbnail_manager import ThumbnailManager
from saurus.sql.pysaurus_program import PysaurusProgram

METRIC = "euclidean"
NB_TREES = 100
NB_NEAR = 20
BLUR_SIZE = 1
ANNOY_SEED = 1234567890

DIM = ImageUtils.THUMBNAIL_DIMENSION
HALF = DIM // 2
SIZE = (DIM, DIM)

def main_old():
    metric = "euclidean"
    nb_trees = 100
    nb_near = 20
    blur = ImageFilter.BoxBlur(1)
    vector_size = DIM * DIM
    max_euclidean = 255 * math.sqrt(vector_size)
    max_dst = max_euclidean * 0.20
    annoy_seed = 1234567890

    application = PysaurusProgram()
    db_name_to_path = {path.title: path for path in application.get_database_paths()}
    db_path = db_name_to_path[DB_NAME]
    ways = DbWays(db_path)
    thumb_sql_path = ways.db_thumb_sql_path
    assert thumb_sql_path.isfile()
    thumb_manager = ThumbnailManager(thumb_sql_path)

    with Profiler("Get pre-computed similarities"):
        with open(ways.db_json_path.path) as json_file:
            content = json.load(json_file)
        groups = {}
        for video in content.get("videos", ()):
            groups.setdefault(video.get("S", None), []).append(
                AbsolutePath(video["f"]).path
            )
        groups.pop(-1)
        groups.pop(None)
        sim_groups = [
            (value, videos) for value, videos in groups.items() if len(videos) > 1
        ]
    print("Similarities", len(sim_groups), file=sys.stderr)
    similarities = {}
    video_to_sim = {}
    nb_similar_videos = 0
    for value, videos in sim_groups:
        videos.sort()
        similarities.setdefault(videos[0], set()).update(videos[1:])
        video_to_sim[videos[0]] = value
        nb_similar_videos += len(videos)
    print("Similar videos", nb_similar_videos, file=sys.stderr)

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
            thumbnail = image.resize(SIZE)
            normalized = thumbnail.filter(blur)
            vector = [round(sum(pixel)/3) for pixel in normalized.getdata()]
            vectors.append((row["filename"], vector))
            bar.update(1)

    assert all(
        len(vector[1]) == vector_size for vector in tqdm(vectors, desc="check vectors")
    )

    # Build Annoy index
    t = AnnoyIndex(vector_size, metric)
    t.set_seed(annoy_seed)
    for i, (filename, vector) in tqdm(
        list(enumerate(vectors)), desc="Add items to Annoy"
    ):
        t.add_item(i, vector)

    with Profiler("Build Annoy trees"):
        t.build(nb_trees)
    with Profiler("Save Annoy to disk"):
        t.save("ignored/test.ann")

    results = [
        (i, t.get_nns_by_item(i, nb_near, include_distances=True))
        for i in trange(len(vectors), desc="Search in Annoy index")
    ]

    output = {}
    for i, (ids, dsts) in results:
        d = {
            vectors[j][0]: dst for j, dst in zip(ids, dsts) if i != j and dst <= max_dst
        }
        if d:
            output[vectors[i][0]] = d

    assert output
    nb_expected_sims = nb_similar_videos
    nb_detected_sims = sum(len(fs) for fs in output.values())
    print("Expected sims", nb_expected_sims, file=sys.stderr)
    print("Detected sims", nb_detected_sims, file=sys.stderr)
    print("Truth rate", nb_expected_sims * 100 / nb_detected_sims, "%", file=sys.stderr)

    with open(f"ignored/results_{metric}_dict.json", "w") as file:
        json.dump(output, file, indent=1)

    with Profiler("Check expected similarities"):
        for filename, linked_filenames in similarities.items():
            assert filename in output, filename
            for linked_filename in sorted(linked_filenames):
                if (
                    linked_filename not in output[filename]
                    and filename not in output[linked_filename]
                ):
                    print("Missing", video_to_sim[filename], file=sys.stderr)
                    print("\t", filename, file=sys.stderr)
                    print("\t", linked_filename, file=sys.stderr)


if __name__ == "__main__":
    with Profiler("main"):
        main_old()
