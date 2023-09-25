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
from abc import ABC, abstractmethod
from ctypes import pointer
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple

import nmslib
import numpy as np
from PIL import ImageFilter
from PIL.Image import Image
from annoy import AnnoyIndex
from tqdm import tqdm, trange

from other.tests.utils_testing import DB_NAME
from pysaurus.core.components import AbsolutePath
from pysaurus.core.fraction import Fraction
from pysaurus.core.modules import ImageUtils
from pysaurus.core.profiling import InlineProfiler, Profiler
from pysaurus.database.db_way_def import DbWays
from pysaurus.database.thubmnail_database.thumbnail_manager import ThumbnailManager
from pysaurus.database.video_similarities.alignment_raptor.alignment import (
    miniature_to_c_sequence,
)
from pysaurus.database.video_similarities.alignment_raptor.symbols import (
    fn_compareSimilarSequences,
)
from pysaurus.database.video_similarities.backend_numpy import SimilarityComparator
from pysaurus.miniature.graph import Graph
from pysaurus.miniature.miniature import Miniature, NumpyMiniature
from saurus.sql.pysaurus_program import PysaurusProgram

SIM_LIMIT = float(Fraction(89, 100))
SIMPLE_MAX_PIXEL_DISTANCE = 255 * 3


class AbstractImageProvider(ABC):
    __slots__ = ()

    @abstractmethod
    def count(self) -> int:
        pass

    @abstractmethod
    def items(self) -> Iterable[Tuple[Any, Image]]:
        pass


class ApproximateComparator:
    __slots__ = ("vectors", "vector_size", "data")
    DIM = 16
    SIZE = (DIM, DIM)

    NB_TREES = 200
    NB_NEAR = 20
    NB_NEAR_NMSLIB = 15
    NMSLIB_POST = 0
    ANNOY_SEED = 1234567890

    def __init__(self, imp: AbstractImageProvider):
        blur = ImageFilter.BoxBlur(1)
        vector_size = 3 * self.DIM * self.DIM
        vectors = []
        with tqdm(total=imp.count(), desc="Get vectors") as bar:
            for i, (identifier, image) in enumerate(imp.items()):
                thumbnail = image.resize(self.SIZE)
                normalized = thumbnail.filter(blur)
                vector = [v for pixel in normalized.getdata() for v in pixel]
                vectors.append((identifier, vector))
                bar.update(1)
        assert all(
            len(vector[1]) == vector_size
            for vector in tqdm(vectors, desc="check vectors")
        )
        self.vectors = vectors
        self.vector_size = vector_size
        self.data = np.asarray([vector[1] for vector in self.vectors], dtype=np.float32)

    def get_comparable_images(self) -> Dict[Any, Dict[Any, float]]:
        vectors = self.vectors
        vector_size = self.vector_size

        nb_trees = self.NB_TREES
        nb_near = self.NB_NEAR
        annoy_seed = self.ANNOY_SEED
        metric = "angular"
        max_angular = math.sqrt(2)
        max_dst = max_angular * 0.3

        # Build Annoy index
        t = AnnoyIndex(vector_size, metric)
        t.set_seed(annoy_seed)
        for i, (filename, vector) in tqdm(
            list(enumerate(vectors)), desc="Add items to Annoy"
        ):
            t.add_item(i, vector)

        with InlineProfiler("Build Annoy trees"):
            t.build(nb_trees)

        # Get nearest neighbors for each vector.
        results = [
            (i, t.get_nns_by_item(i, nb_near, include_distances=True))
            for i in trange(len(vectors), desc="Search in Annoy index")
        ]

        output = {}
        for i, (near_indices, near_distances) in results:
            d = {
                vectors[j][0]: dst
                for j, dst in zip(near_indices, near_distances)
                if i != j and dst <= max_dst
            }
            if d:
                output[vectors[i][0]] = d
        return output

    def get_comparable_images_euclidian(self) -> Dict[Any, Dict[Any, float]]:
        vectors = self.vectors
        vector_size = self.vector_size

        nb_trees = self.NB_TREES
        nb_near = self.NB_NEAR
        annoy_seed = self.ANNOY_SEED
        metric = "euclidean"
        max_euclidian = 255 * math.sqrt(vector_size)
        max_dst = max_euclidian * 0.175

        # Build Annoy index
        t = AnnoyIndex(vector_size, metric)
        t.set_seed(annoy_seed)
        for i, (filename, vector) in tqdm(
            list(enumerate(vectors)), desc="Add items to Annoy"
        ):
            t.add_item(i, vector)

        with InlineProfiler("Build Annoy trees"):
            t.build(nb_trees)

        # Get nearest neighbors for each vector.
        results = [
            (i, t.get_nns_by_item(i, nb_near, include_distances=True))
            for i in trange(len(vectors), desc="Search in Annoy index")
        ]

        output = {}
        for i, (near_indices, near_distances) in results:
            d = {
                vectors[j][0]: dst
                for j, dst in zip(near_indices, near_distances)
                if i != j and dst <= max_dst
            }
            if d:
                output[vectors[i][0]] = d
        return output

    def use_nmslib(self):
        data = self.data

        index = nmslib.init(method="hnsw", space="cosinesimil")
        index.addDataPointBatch(data)
        index.createIndex({"post": self.NMSLIB_POST}, print_progress=True)

        neighbours = [
            index.knnQuery(data[i], k=self.NB_NEAR_NMSLIB)
            for i in trange(len(self.vectors), desc="find neighbors")
        ]
        output = {
            self.vectors[i][0]: {
                self.vectors[j][0]: dst for j, dst in zip(ids, distances)
            }
            for i, (ids, distances) in enumerate(neighbours)
        }
        return output

    def use_nmslib_euclidean(self):
        data = self.data

        index = nmslib.init(method="hnsw", space="l2")
        index.addDataPointBatch(data)
        index.createIndex({"post": self.NMSLIB_POST}, print_progress=True)

        neighbours = [
            index.knnQuery(data[i], k=self.NB_NEAR_NMSLIB)
            for i in trange(len(self.vectors), desc="find neighbors")
        ]
        output = {
            self.vectors[i][0]: {
                self.vectors[j][0]: dst for j, dst in zip(ids, distances)
            }
            for i, (ids, distances) in enumerate(neighbours)
        }
        return output


def compare_images(
    imp: AbstractImageProvider, output: Dict[Any, Sequence[Any]]
) -> List[Set[Any]]:
    nb_images = imp.count()
    numpy_miniatures = {}
    with tqdm(total=nb_images, desc="Generate numpy miniatures") as pbar:
        for identifier, image in imp.items():
            numpy_miniatures[identifier] = NumpyMiniature.from_image(
                image.resize(ImageUtils.THUMBNAIL_SIZE)
            )
            pbar.update(1)
    assert len(numpy_miniatures) == nb_images

    graph = Graph()
    nb_todo = sum(len(d) for d in output.values())
    sim_cmp = SimilarityComparator(
        SIM_LIMIT, ImageUtils.THUMBNAIL_DIMENSION, ImageUtils.THUMBNAIL_DIMENSION
    )
    with tqdm(total=nb_todo, desc="Make real comparisons using Numpy") as bar:
        for filename, linked_filenames in output.items():
            p1 = numpy_miniatures[filename]
            for linked_filename in linked_filenames:
                p2 = numpy_miniatures[linked_filename]
                if sim_cmp.are_similar(p1, p2):
                    graph.connect(filename, linked_filename)
                bar.update(1)

    groups = [group for group in graph.pop_groups() if len(group) > 1]
    return groups


class CppSimilarityComparator:
    __slots__ = ("max_dst_score", "limit", "width", "height")

    def __init__(self, limit, width, height):
        self.width = width
        self.height = height
        self.limit = limit
        self.max_dst_score = SIMPLE_MAX_PIXEL_DISTANCE * width * height

    def are_similar(self, p1, p2) -> bool:
        return (
            fn_compareSimilarSequences(
                p1, p2, self.width, self.height, self.max_dst_score
            )
            >= self.limit
        )


def compare_images_native(
    imp: AbstractImageProvider, output: Dict[Any, Sequence[Any]]
) -> List[Set[Any]]:
    nb_images = imp.count()
    miniatures = {}
    with tqdm(total=nb_images, desc="Generate numpy miniatures") as pbar:
        for identifier, image in imp.items():
            miniatures[identifier] = Miniature.from_image(
                image.resize(ImageUtils.THUMBNAIL_SIZE)
            )
            pbar.update(1)
    assert len(miniatures) == nb_images

    with InlineProfiler("Generate native sequences"):
        native_sequences = {
            identifier: miniature_to_c_sequence(sequence)
            for identifier, sequence in miniatures.items()
        }
        native_sequence_pointers = {
            identifier: pointer(sequence)
            for identifier, sequence in native_sequences.items()
        }

    graph = Graph()
    nb_todo = sum(len(d) for d in output.values())
    sim_cmp = CppSimilarityComparator(
        SIM_LIMIT, ImageUtils.THUMBNAIL_DIMENSION, ImageUtils.THUMBNAIL_DIMENSION
    )
    with tqdm(total=nb_todo, desc="Make real comparisons using Numpy") as bar:
        for filename, linked_filenames in output.items():
            p1 = native_sequence_pointers[filename]
            for linked_filename in linked_filenames:
                p2 = native_sequence_pointers[linked_filename]
                if sim_cmp.are_similar(p1, p2):
                    graph.connect(filename, linked_filename)
                bar.update(1)

    groups = [group for group in graph.pop_groups() if len(group) > 1]
    return groups


class LocalImageProvider(AbstractImageProvider):
    def __init__(self):
        application = PysaurusProgram()
        db_name_to_path = {
            path.title: path for path in application.get_database_paths()
        }
        db_path = db_name_to_path[DB_NAME]
        self.ways = DbWays(db_path)
        thumb_sql_path = self.ways.db_thumb_sql_path
        assert thumb_sql_path.isfile()
        self.thumb_manager = ThumbnailManager(thumb_sql_path)
        self.nb_images = self.thumb_manager.thumb_db.query_one(
            "SELECT COUNT(filename) FROM video_to_thumbnail"
        )[0]

    def count(self) -> int:
        return self.nb_images

    def items(self) -> Iterable[Tuple[Any, Image]]:
        for row in self.thumb_manager.thumb_db.query(
            "SELECT filename, thumbnail FROM video_to_thumbnail"
        ):
            yield row["filename"], ImageUtils.from_blob(row["thumbnail"])


class Checker:
    __slots__ = ("video_to_sim", "sim_groups", "ways")

    def __init__(self, ways):
        with InlineProfiler("Get pre-computed similarities"):
            with open(ways.db_json_path.path) as json_file:
                content = json.load(json_file)
            groups = {}
            for video in content.get("videos", ()):
                groups.setdefault(video.get("S", None), []).append(
                    AbsolutePath(video["f"]).path
                )
            groups.pop(-1)
            groups.pop(None)
            sim_groups = sorted(
                (
                    (value, sorted(videos))
                    for value, videos in groups.items()
                    if len(videos) > 1
                ),
                key=lambda c: c[0],
            )
            video_to_sim = {
                filename: value
                for value, filenames in sim_groups
                for filename in filenames
            }

        self.ways = ways
        self.video_to_sim = video_to_sim
        self.sim_groups = sim_groups

    def save(self, output, metric):
        with open(f"ignored/results_{metric}_dict.json", "w") as file:
            json.dump(output, file, indent=1)

    def check(self, output, new_sim_groups):
        video_to_sim = self.video_to_sim
        sim_groups = self.sim_groups

        print(
            "Comparisons to do", sum(len(d) for d in output.values()), file=sys.stderr
        )

        nb_similar_videos = sum(len(videos) for _, videos in sim_groups)
        print("Similarities", len(sim_groups), file=sys.stderr)
        print("Similar videos", nb_similar_videos, file=sys.stderr)
        if new_sim_groups:
            nb_new_similar_videos = sum(len(group) for group in new_sim_groups)
            nb_new_similar_groups = len(new_sim_groups)
            print("New similarities", nb_new_similar_groups, file=sys.stderr)
            print("New similar videos", nb_new_similar_videos, file=sys.stderr)

        with InlineProfiler("Check new sim groups"):
            for group in new_sim_groups:
                old_sims = {video_to_sim.get(filename, -1) for filename in group}
                if len(old_sims) != 1:
                    print("Bad group", file=sys.stderr)
                    for filename in group:
                        print(
                            "\t",
                            video_to_sim.get(filename, -1),
                            filename,
                            file=sys.stderr,
                        )
                else:
                    (sim,) = list(old_sims)
                    if sim == -1:
                        print("New group", file=sys.stderr)
                        for filename in group:
                            print("\t", filename, file=sys.stderr)

        with Profiler("Check expected similarities"):
            for sim_id, videos in sim_groups:
                filename, *linked_filenames = videos
                for linked_filename in linked_filenames:
                    has_l = filename in output and linked_filename in output[filename]
                    has_r = (
                        linked_filename in output
                        and filename in output[linked_filename]
                    )
                    if not has_l and not has_r:
                        print("Missing", sim_id, file=sys.stderr)
                        print("\t", filename, file=sys.stderr)
                        print("\t", linked_filename, file=sys.stderr)


def main_new():
    imp = LocalImageProvider()
    chk = Checker(imp.ways)
    ac = ApproximateComparator(imp)

    output_angular = ac.use_nmslib()
    chk.check(output_angular, [])

    output_euclidian = ac.use_nmslib_euclidean()
    chk.check(output_euclidian, [])

    all_filenames = sorted(set(output_angular) | set(output_euclidian))
    combined = {
        filename: sorted(
            set(output_angular.get(filename, ()))
            & set(output_euclidian.get(filename, ()))
        )
        for filename in all_filenames
    }
    chk.check(combined, [])

    final_output = {}
    similarities = compare_images_native(imp, combined)
    for group in similarities:
        group = list(group)
        final_output[group[0]] = set(group[1:])
    chk.check(final_output, similarities)


if __name__ == "__main__":
    with Profiler("main"):
        main_new()
