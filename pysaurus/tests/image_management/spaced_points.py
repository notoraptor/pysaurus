from typing import Union


class SpacedPoints:
    """
    Number of points and related interval size for some lengths:
    Length 32:
        2: 30
    Length 64:
        2: 62
        4: 20
        8: 8
        10: 6
        22: 2
    Length 256:
        2: 254
        4: 84
        6: 50
        16: 16
        18: 14
        52: 4
        86: 2
    Length 1021:
        5: 254
        13: 84
        21: 50
        61: 16
        69: 14
        205: 4
        341: 2
    Length 1024:
        2: 1022
        4: 340
        12: 92
        32: 32
        34: 30
        94: 10
        342: 2
    """

    __slots__ = 'd',
    _MAP_POINTS = {}

    def __init__(self, length=256, nb_points=6):
        if length not in self._MAP_POINTS:
            self._MAP_POINTS[length] = self.available_points_and_spaces(length)
        points = self._MAP_POINTS[length]
        assert nb_points in points, tuple(points)
        self.d = points[nb_points] + 1

    def nearest_point(self, value: Union[int, float]):
        # 0 <= value < interval length
        i = int(value // self.d)
        before = i * self.d
        after = (i + 1) * self.d
        if value - before < after - value:
            return before
        return after

    @classmethod
    def _space_between_points(cls, interval_length, nb_points):
        # we assume 2 <= k < interval_length
        top = interval_length - nb_points
        bottom = nb_points - 1
        return None if top % (2 * bottom) else top // bottom

    @classmethod
    def available_points_and_spaces(cls, interval_length):
        pt_to_il = {}
        for pt in range(2, interval_length):
            il = cls._space_between_points(interval_length, pt)
            if il:
                pt_to_il[pt] = il
        return pt_to_il
