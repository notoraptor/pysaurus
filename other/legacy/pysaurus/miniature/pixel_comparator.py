import math
from abc import abstractmethod
from typing import Union

pi = math.pi
sin = math.sin


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


def f(x):
    return ((64 * x**2 - x**3 / 6) * 3) / (128**2)


def f2(x):
    return (x * pi / 128 - sin(x * pi / 128)) * 256 / (2 * pi)


def f3(x):
    return f2(f2(x))


class DistancePixelComparator(AbstractPixelComparator):
    __slots__ = "threshold", "limit", "normalizer"

    def __init__(self, similarity_percent: Union[int, float], normalizer=0):
        self.threshold = (100 - similarity_percent) / 100
        self.limit = self.threshold * 255 * math.sqrt(3)
        self.normalizer = [
            self._normalize_data_0,
            self._normalize_data_1,
            self._normalize_data_2,
            self._normalize_data_3,
        ][normalizer]

    def normalize_data(self, data, width):
        return self.normalizer(data, width)

    def _normalize_data_0(self, data, width):
        return list(data)

    def _normalize_data_1(self, data, width):
        return [(round(f(r)), round(f(g)), round(f(b))) for r, g, b in data]

    def _normalize_data_2(self, data, width):
        return [(round(f2(r)), round(f2(g)), round(f2(b))) for r, g, b in data]

    def _normalize_data_3(self, data, width):
        return [(round(f3(r)), round(f3(g)), round(f3(b))) for r, g, b in data]

    def pixels_are_close(self, data, i, j, width):
        r1, g1, b1 = data[i]
        r2, g2, b2 = data[j]
        distance = math.sqrt(
            (r1 - r2) * (r1 - r2) + (g1 - g2) * (g1 - g2) + (b1 - b2) * (b1 - b2)
        )
        return distance <= self.limit

    def common_color(self, data, indices, width):
        return (
            sum(data[i][0] for i in indices) / len(indices),
            sum(data[i][1] for i in indices) / len(indices),
            sum(data[i][2] for i in indices) / len(indices),
        )
