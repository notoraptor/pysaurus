from abc import ABC, abstractmethod
from typing import Any

from pysaurus.core.informer import Information
from pysaurus.core.notifications import Message
from pysaurus.imgsimsearch.abstract_image_provider import AbstractImageProvider


class AbstractApproximateComparator(ABC):
    __slots__ = ("vectors", "vector_size", "notifier", "indices_to_compare")
    DIM = 16
    SIZE = (DIM, DIM)
    WEIGHT_LENGTH = 8
    NB_NEAR = 12

    def __init__(self, imp: AbstractImageProvider):
        weight_length = self.WEIGHT_LENGTH
        self.notifier = Information.notifier()
        vector_size = 3 * self.DIM * self.DIM + weight_length
        vectors = []
        indices_to_compare = []
        for i, (identifier, image) in enumerate(
            self.notifier.tasks(imp.items(), "get vectors", imp.count())
        ):
            thumbnail = image.resize(self.SIZE)
            vector = [v for pixel in thumbnail.getdata() for v in pixel] + (
                [imp.length(identifier)] * weight_length
            )
            assert len(vector) == vector_size
            vectors.append((identifier, vector))
            if imp.similarity(identifier) is None:
                indices_to_compare.append(i)
        self.vectors = vectors
        self.vector_size = vector_size
        self.indices_to_compare = indices_to_compare
        self.notifier.notify(
            Message(f"To compare: {len(self.indices_to_compare)} video(s).")
        )

    @abstractmethod
    def get_comparable_images_cos(self) -> dict[Any, dict[Any, float]]:
        raise NotImplementedError()
