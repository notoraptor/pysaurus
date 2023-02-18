from typing import Tuple

from pysaurus.miniature.pixel_comparator import AbstractPixelComparator


class ColorClassPixelComparator(AbstractPixelComparator):
    def __init__(self, interval_length: int):
        self.interval_length = interval_length

    def _map_pixel(self, pixel: Tuple[int, int, int]) -> Tuple:
        return tuple(
            int(v // self.interval_length) * self.interval_length for v in pixel
        )

    def normalize_data(self, data, width):
        return list(data)

    def pixels_are_close(self, data, i, j, width):
        return self._map_pixel(data[i]) == self._map_pixel(data[j])

    def common_color(self, data, indices, width):
        return self._map_pixel(data[next(iter(indices))])
