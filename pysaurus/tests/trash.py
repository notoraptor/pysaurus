from typing import Union


class SpacedPoints:
    """
    for interval length = 256, we have available points:
    k = 2;  c = 8;      l = 254
    k = 4;  c = 64;     l = 84
    k = 6;  c = 216;    l = 50
    k = 16; c = 4096;   l = 16
    k = 18; c = 5832;   l = 14
    k = 52; c = 140608; l = 4
    k = 86; c = 636056; l = 2
    """

    __slots__ = 'd', 'index_of', 'near_indices_of'
    _MAP_POINTS = {}

    def __init__(self, length=256, nb_points=6):
        if length not in self._MAP_POINTS:
            self._MAP_POINTS[length] = self._available_points_and_spaces(length)
        points = self._MAP_POINTS[length]
        assert nb_points in points, tuple(points)
        self.d = points[nb_points] + 1
        self.index_of = [self.nearest_index(value) for value in range(length)]
        self.near_indices_of = [self.nearest_indices(value, length) for value in range(length)]

    def nearest_index(self, value: Union[int, float]):
        # 0 <= value < interval length
        i = int(value // self.d)
        before = i * self.d
        after = (i + 1) * self.d
        if value - before < after - value:
            return i
        return i + 1

    def nearest_indices(self, value: Union[int, float], length):
        return sorted({
            self.nearest_index(max(0, value - (self.d - 1) // 2)),
            self.nearest_index(value),
            self.nearest_index(min(length - 1, value + (self.d - 1) // 2))
        })

    def nearest_point(self, value: Union[int, float]):
        # 0 <= value < interval length
        i = int(value // self.d)
        before = i * self.d
        after = (i + 1) * self.d
        if value - before < after - value:
            return before
        return after

    def nearest_points(self, values: Union[list, tuple]):
        return type(values)(self.nearest_point(value) for value in values)

    @classmethod
    def _space_between_points(cls, interval_length, nb_points):
        # 2 <= k < interval_length
        top = interval_length - nb_points
        bottom = nb_points - 1
        if top % (2 * bottom):
            return None
        return top // bottom

    @classmethod
    def _available_points_and_spaces(cls, interval_length):
        pt_to_il = {}
        for pt in range(2, interval_length):
            il = cls._space_between_points(interval_length, pt)
            if il:
                pt_to_il[pt] = il
        return pt_to_il