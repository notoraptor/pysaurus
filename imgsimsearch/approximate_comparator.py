import nmslib
import numpy as np
from PIL import ImageFilter
from tqdm import tqdm, trange

from imgsimsearch.abstract_image_provider import AbstractImageProvider


class ApproximateComparator:
    __slots__ = ("vectors", "vector_size", "data")
    DIM = 16
    SIZE = (DIM, DIM)

    NB_NEAR_NMSLIB = 15
    NMSLIB_POST = 0

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

    def get_comparable_images_cos(self):
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

    def get_comparable_images_euc(self):
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
