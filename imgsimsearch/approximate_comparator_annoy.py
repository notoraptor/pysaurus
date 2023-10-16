import math
from typing import Any, Dict

import numpy as np
from PIL import ImageFilter
from annoy import AnnoyIndex
from tqdm import tqdm, trange

from imgsimsearch.abstract_image_provider import AbstractImageProvider
from pysaurus.core.profiling import InlineProfiler


class ApproximateComparatorAnnoy:
    __slots__ = ("vectors", "vector_size", "data")
    DIM = 16
    SIZE = (DIM, DIM)

    NB_TREES = 200
    NB_NEAR = 20
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
