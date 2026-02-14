from typing import Any

import math

import numpy as np

from pysaurus.imgsimsearch.abstract_approximate_comparator import (
    AbstractApproximateComparator,
)


class ApproximateComparatorNumpy(AbstractApproximateComparator):
    """Exact nearest neighbor search using NumPy brute force.

    Drop-in replacement for ApproximateComparatorAnnoy.
    No external dependencies beyond NumPy.
    Deterministic (no random trees).
    """

    def get_comparable_images_cos(self) -> dict[Any, dict[Any, float]]:
        max_angular = math.sqrt(2)
        max_dst = max_angular * 0.1875
        return self._compare_angular(max_dst)

    def _compare_angular(self, max_dst) -> dict[Any, dict[Any, float]]:
        vectors = self.vectors
        nb_near = self.NB_NEAR

        # Build normalized matrix for cosine similarity
        data = np.array([v for _, v in vectors], dtype=np.float64)
        norms = np.linalg.norm(data, axis=1, keepdims=True)
        norms[norms == 0] = 1
        normalized = data / norms

        output = {}
        for i in self.notifier.tasks(self.indices_to_compare, desc="Search with NumPy"):
            # Cosine similarities with all vectors
            cos_sims = normalized[i] @ normalized.T
            np.clip(cos_sims, -1, 1, out=cos_sims)
            # Angular distance: same metric as Annoy "angular"
            angular_dists = np.sqrt(2.0 * (1.0 - cos_sims))
            # Exclude self
            angular_dists[i] = np.inf

            # Find top K nearest neighbors
            if len(angular_dists) <= nb_near:
                near_indices = np.arange(len(angular_dists))
            else:
                near_indices = np.argpartition(angular_dists, nb_near)[:nb_near]

            d = {
                vectors[j][0]: float(angular_dists[j])
                for j in near_indices
                if angular_dists[j] <= max_dst
            }
            if d:
                output[vectors[i][0]] = d

        return output
