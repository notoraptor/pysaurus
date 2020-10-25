from typing import Union, List


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


class LinearFunction:
    __slots__ = 'a', 'b'

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __str__(self):
        return f"(x: {self.a}*x {'' if self.b < 0 else '+'}{self.b})"

    def __call__(self, x):
        return self.a * x + self.b

    def latest_intersection(self, values: List[Union[int, float]]):
        n = len(values)
        y_values = sorted(values)
        direction = None
        for i in range(n):
            x = n - i - 1
            v = y_values[x]
            y = self(x)
            if v == y:
                print('Stopped from behind (==) at', i + 1, '/', len(values))
                return v
            current_direction = v > y
            if direction is None:
                direction = current_direction
            elif direction is not current_direction:
                print('Stopped from behind (!=) at', i + 1, '/', len(values))
                return v
        raise ValueError(f'Unable to get latest intersection {self} from {[self(c) for c in range(n)]} to {y_values}')

    @classmethod
    def get_linear_regression(cls, values: list):
        n = len(values)
        y_values = sorted(values)
        x_values = list(range(n))
        average_x = sum(x_values) / n
        average_y = sum(y_values) / n
        var_x = (sum(x ** 2 for x in x_values) / n) - average_x ** 2
        cov_xy = (sum(x * y for x, y in zip(x_values, y_values)) / n) - average_x * average_y
        a = cov_xy / var_x
        b = average_y - a * average_x
        return LinearFunction(a, b)

    @classmethod
    def get_line(cls, x1, y1, x2, y2):
        a = (y2 - y1) / (x2 - x1)
        b = y1 - a * x1
        return LinearFunction(a, b)


def main():
    for l in (32, 64, 128, 256, 1024):
        pt_to_il = SpacedPoints.available_points_and_spaces(l)
        print(f'Length {l}:')
        for pt, il in sorted(pt_to_il.items()):
            print(f'\t{pt}: {il}')


if __name__ == '__main__':
    main()
