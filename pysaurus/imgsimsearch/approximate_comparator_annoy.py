from typing import Any

import math
import logging

try:
    from annoy import AnnoyIndex
except ImportError as exc:
    logging.exception("annoy not available", exc_info=exc)
    # raise Exception("annoy not available") from exc

from pysaurus.core.profiling import Profiler
from pysaurus.imgsimsearch.abstract_approximate_comparator import (
    AbstractApproximateComparator,
)


class ApproximateComparatorAnnoy(AbstractApproximateComparator):
    NB_TREES = 200
    ANNOY_SEED = 1234567890

    def get_comparable_images_cos(self) -> dict[Any, dict[Any, float]]:
        metric = "angular"
        max_angular = math.sqrt(2)
        max_dst = max_angular * 0.1875
        return self._compare(metric, max_dst)

    def get_comparable_images_euc(self) -> dict[Any, dict[Any, float]]:
        metric = "euclidean"
        max_euclidian = 255 * math.sqrt(self.vector_size)
        max_dst = max_euclidian * 0.2
        return self._compare(metric, max_dst)

    def _compare(self, metric, max_dst) -> dict[Any, dict[Any, float]]:
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
        # NB: For full comparison,
        # use range(len(vectors)) instead of self.indices_to_compare
        results = [
            (i, t.get_nns_by_item(i, nb_near, include_distances=True))
            for i in self.notifier.tasks(
                self.indices_to_compare, desc="Search in Annoy index"
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
