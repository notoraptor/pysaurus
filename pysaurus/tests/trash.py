import math
from typing import Union, List

from pysaurus.core.native.video_raptor.miniature import Miniature


def _clip_color(value):
    return min(max(0, value), 255)


def equalize(data):
    if not isinstance(data, (list, tuple)):
        data = list(data)
    grays = sorted({int(sum(p) / 3) for p in data})
    if len(grays) < 2:
        return data
    best_distance = 255 / (len(grays) - 1)
    new_grays = [0]
    for i in range(1, len(grays)):
        new_grays.append(new_grays[i - 1] + best_distance)
    new_grays = [round(gray) for gray in new_grays]
    assert new_grays[-1] == 255, new_grays[-1]
    gray_to_index = {gray: index for index, gray in enumerate(grays)}
    output = []
    for pixel in data:
        r, g, b = pixel
        gray = int((r + g + b) / 3)
        index = gray_to_index[gray]
        new_gray = new_grays[index]
        distance = new_gray - gray
        new_color = _clip_color(r + distance), _clip_color(g + distance), _clip_color(b + distance)
        # assert int(sum(new_color) / 3) == new_gray, (int(sum(new_color) / 3), new_gray, gray, new_color, pixel)
        output.append(new_color)
    return output


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
    for l in (32, 64, 128, 256, 1024 - 4 + 1, 1024):
        pt_to_il = SpacedPoints.available_points_and_spaces(l)
        print(f'Length {l}:')
        for pt, il in sorted(pt_to_il.items()):
            print(f'\t{pt}: {il}')


if __name__ == '__main__':
    main()


class MiniatureComparator:
    SIMPLE_MAX_PIXEL_DISTANCE = 255 * 3
    V = SIMPLE_MAX_PIXEL_DISTANCE
    B = V / 2.0
    V_PLUS_B = V + B

    @classmethod
    def moderate(cls, x):
        return cls.V_PLUS_B * x / (x + cls.B)

    @classmethod
    def pixel_distance(cls, p1: Miniature, index_p1: int, p2: Miniature, index_p2: int):
        return cls.moderate(abs(p1.r[index_p1] - p2.r[index_p2]) + abs(p1.g[index_p1] - p2.g[index_p2]) + abs(
            p1.b[index_p1] - p2.b[index_p2]))

    @classmethod
    def macro_pixel_distance(cls, p1, x, y, p2, local_x, local_y, width):
        return cls.pixel_distance(p1, x + y * width, p2, local_x + local_y * width)

    @classmethod
    def compare_basic(cls, p1: Miniature, p2: Miniature, width: int, height: int,
                      maximum_similarity_score: Union[int, float]):
        # total_distance = sum(abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2) for (r1, g1, b1), (r2, g2, b2) in zip(p1.data(), p2.data()))
        total_distance = (
                sum(abs(r1 - r2) for r1, r2 in zip(p1.r, p2.r))
                + sum(abs(g1 - g2) for g1, g2 in zip(p1.g, p2.g))
                + sum(abs(b1 - b2) for b1, b2 in zip(p1.b, p2.b))
        )
        return (maximum_similarity_score - total_distance) / maximum_similarity_score

    @classmethod
    def compare_better(cls, p1: Miniature, p2: Miniature, width: int, height: int,
                       maximum_similarity_score: Union[int, float]):
        total_distance = sum(
            math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)
            for (r1, g1, b1), (r2, g2, b2) in zip(p1.data(), p2.data())
        )
        return (maximum_similarity_score - total_distance) / maximum_similarity_score

    @classmethod
    def compare_faster(cls, p1, p2, width, height, maximum_similarity_score):
        # x, y:
        total_distance = (
                min(  # 0, 0
                    cls.macro_pixel_distance(p1, 0, 0, p2, 0, 0, width),
                    cls.macro_pixel_distance(p1, 0, 0, p2, 1, 0, width),
                    cls.macro_pixel_distance(p1, 0, 0, p2, 0, 1, width),
                    cls.macro_pixel_distance(p1, 0, 0, p2, 1, 1, width))
                + min(  # width - 1, 0
            cls.macro_pixel_distance(p1, width - 1, 0, p2, width - 2, 0, width),
            cls.macro_pixel_distance(p1, width - 1, 0, p2, width - 1, 0, width),
            cls.macro_pixel_distance(p1, width - 1, 0, p2, width - 2, 1, width),
            cls.macro_pixel_distance(p1, width - 1, 0, p2, width - 1, 1, width))
                + min(  # 0, height - 1
            cls.macro_pixel_distance(p1, 0, height - 1, p2, 0, height - 1, width),
            cls.macro_pixel_distance(p1, 0, height - 1, p2, 1, height - 1, width),
            cls.macro_pixel_distance(p1, 0, height - 1, p2, 0, height - 2, width),
            cls.macro_pixel_distance(p1, 0, height - 1, p2, 1, height - 2, width))
                + min(  # width - 1, height - 1
            cls.macro_pixel_distance(p1, width - 1, height - 1, p2, width - 2, height - 1, width),
            cls.macro_pixel_distance(p1, width - 1, height - 1, p2, width - 1, height - 1, width),
            cls.macro_pixel_distance(p1, width - 1, height - 1, p2, width - 2, height - 2, width),
            cls.macro_pixel_distance(p1, width - 1, height - 1, p2, width - 1, height - 2, width))
        )
        for x in range(1, width - 1):
            # x, 0
            total_distance += min(
                cls.macro_pixel_distance(p1, x, 0, p2, x - 1, 0, width),
                cls.macro_pixel_distance(p1, x, 0, p2, x, 0, width),
                cls.macro_pixel_distance(p1, x, 0, p2, x + 1, 0, width),
                cls.macro_pixel_distance(p1, x, 0, p2, x - 1, 1, width),
                cls.macro_pixel_distance(p1, x, 0, p2, x, 1, width),
                cls.macro_pixel_distance(p1, x, 0, p2, x + 1, 1, width))
            # x, height - 1
            total_distance += min(
                cls.macro_pixel_distance(p1, x, height - 1, p2, x - 1, height - 1, width),
                cls.macro_pixel_distance(p1, x, height - 1, p2, x, height - 1, width),
                cls.macro_pixel_distance(p1, x, height - 1, p2, x + 1, height - 1, width),
                cls.macro_pixel_distance(p1, x, height - 1, p2, x - 1, height - 2, width),
                cls.macro_pixel_distance(p1, x, height - 1, p2, x, height - 2, width),
                cls.macro_pixel_distance(p1, x, height - 1, p2, x + 1, height - 2, width))
        for y in range(1, height - 1):
            # 0, y
            total_distance += min(
                cls.macro_pixel_distance(p1, 0, y, p2, 0, y - 1, width),
                cls.macro_pixel_distance(p1, 0, y, p2, 1, y - 1, width),
                cls.macro_pixel_distance(p1, 0, y, p2, 0, y, width),
                cls.macro_pixel_distance(p1, 0, y, p2, 1, y, width),
                cls.macro_pixel_distance(p1, 0, y, p2, 0, y + 1, width),
                cls.macro_pixel_distance(p1, 0, y, p2, 1, y + 1, width))
            # width - 1, y
            total_distance += min(
                cls.macro_pixel_distance(p1, width - 1, y, p2, width - 2, y - 1, width),
                cls.macro_pixel_distance(p1, width - 1, y, p2, width - 1, y - 1, width),
                cls.macro_pixel_distance(p1, width - 1, y, p2, width - 2, y, width),
                cls.macro_pixel_distance(p1, width - 1, y, p2, width - 1, y, width),
                cls.macro_pixel_distance(p1, width - 1, y, p2, width - 2, y + 1, width),
                cls.macro_pixel_distance(p1, width - 1, y, p2, width - 1, y + 1, width))
        # x in [1; width - 2], y in [1; height - 2]
        remaining_size = (width - 2) * (height - 2)
        for index in range(0, remaining_size):
            x = index % (width - 2) + 1
            y = index // (width - 2) + 1
            total_distance += min(
                cls.macro_pixel_distance(p1, x, y, p2, x - 1, y - 1, width),
                cls.macro_pixel_distance(p1, x, y, p2, x, y - 1, width),
                cls.macro_pixel_distance(p1, x, y, p2, x + 1, y - 1, width),
                cls.macro_pixel_distance(p1, x, y, p2, x - 1, y, width),
                cls.macro_pixel_distance(p1, x, y, p2, x, y, width),
                cls.macro_pixel_distance(p1, x, y, p2, x + 1, y, width),
                cls.macro_pixel_distance(p1, x, y, p2, x - 1, y + 1, width),
                cls.macro_pixel_distance(p1, x, y, p2, x, y + 1, width),
                cls.macro_pixel_distance(p1, x, y, p2, x + 1, y + 1, width))
        return (maximum_similarity_score - total_distance) / maximum_similarity_score
