import math
from typing import Any, Dict

from PIL import ImageFilter
from annoy import AnnoyIndex

from other.imgsimsearch.abstract_image_provider import AbstractImageProvider
from pysaurus.core.informer import Informer
from pysaurus.core.profiling import Profiler


class ApproximateComparatorAnnoy:
    __slots__ = ("vectors", "vector_size", "notifier")
    DIM = 16
    SIZE = (DIM, DIM)
    WEIGHT_LENGTH = 8

    NB_TREES = 200
    NB_NEAR = 12
    ANNOY_SEED = 1234567890

    def __init__(self, imp: AbstractImageProvider):
        weight_length = self.WEIGHT_LENGTH
        self.notifier = Informer.default()
        blur = ImageFilter.BoxBlur(1)
        vector_size = 3 * self.DIM * self.DIM + weight_length
        vectors = []
        for i, (identifier, image) in enumerate(
            self.notifier.tasks(imp.items(), "get vectors", imp.count())
        ):
            thumbnail = image.resize(self.SIZE)
            # normalized = thumbnail.filter(blur)
            normalized = thumbnail
            vector = [v for pixel in normalized.getdata() for v in pixel] + (
                [imp.length(identifier)] * weight_length
            )
            assert len(vector) == vector_size
            vectors.append((identifier, vector))
        self.vectors = vectors
        self.vector_size = vector_size

    def get_comparable_images_cos(self) -> Dict[Any, Dict[Any, float]]:
        metric = "angular"
        max_angular = math.sqrt(2)
        max_dst = max_angular * 0.1875
        return self._compare(metric, max_dst)

    def get_comparable_images_euc(self) -> Dict[Any, Dict[Any, float]]:
        metric = "euclidean"
        max_euclidian = 255 * math.sqrt(self.vector_size)
        max_dst = max_euclidian * 0.2
        return self._compare(metric, max_dst)

    def _compare(self, metric, max_dst) -> Dict[Any, Dict[Any, float]]:
        vectors = self.vectors
        nb_near = self.NB_NEAR

        # Build Annoy index
        t = AnnoyIndex(self.vector_size, metric)
        t.set_seed(self.ANNOY_SEED)
        for i, (filename, vector) in self.notifier.tasks(
            list(enumerate(vectors)), desc="Add items to Annoy"
        ):
            t.add_item(i, vector)

        with Profiler("Build Annoy trees"):
            t.build(self.NB_TREES)

        # Get nearest neighbors for each vector.
        results = [
            (i, t.get_nns_by_item(i, nb_near, include_distances=True))
            for i in self.notifier.tasks(
                range(len(vectors)), desc="Search in Annoy index"
            )
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
