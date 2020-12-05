import math
from abc import abstractmethod
from typing import Union, Tuple


class AbstractPixelComparator:
    __slots__ = ()

    @abstractmethod
    def normalize_data(self, data, width):
        raise NotImplementedError()

    @abstractmethod
    def pixels_are_close(self, data, i, j, width):
        raise NotImplementedError()

    @abstractmethod
    def common_color(self, data, indices, width):
        raise NotImplementedError()


class DistancePixelComparator(AbstractPixelComparator):
    __slots__ = 'threshold', 'limit'

    def __init__(self, similarity_percent: Union[int, float]):
        self.threshold = (100 - similarity_percent) / 100
        self.limit = self.threshold * 255 * math.sqrt(3)

    def normalize_data(self, data, width):
        return list(data)

    def pixels_are_close(self, data, i, j, width):
        r1, g1, b1 = data[i]
        r2, g2, b2 = data[j]
        distance = math.sqrt((r1 - r2) * (r1 - r2) + (g1 - g2) * (g1 - g2) + (b1 - b2) * (b1 - b2))
        return distance <= self.limit

    def common_color(self, data, indices, width):
        nb_indices = len(indices)
        sum_r = 0
        sum_g = 0
        sum_b = 0
        for index in indices:
            r, g, b = data[index]
            sum_r += r
            sum_g += g
            sum_b += b
        return sum_r / nb_indices, sum_g / nb_indices, sum_b / nb_indices


class ColorClassPixelComparator(AbstractPixelComparator):

    def __init__(self, interval_length: int):
        self.interval_length = interval_length

    def _map_pixel(self, pixel: Tuple[int, int, int]) -> Tuple:
        return tuple(
            int(v // self.interval_length) * self.interval_length
            for v in pixel
        )

    def normalize_data(self, data, width):
        return list(data)

    def pixels_are_close(self, data, i, j, width):
        return self._map_pixel(data[i]) == self._map_pixel(data[j])

    def common_color(self, data, indices, width):
        return self._map_pixel(data[next(iter(indices))])
