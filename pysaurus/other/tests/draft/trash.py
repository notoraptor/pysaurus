import math
from typing import Union, List

from pysaurus.core.miniature import Miniature
from pysaurus.other.tests.image_management.elements.spaced_points import SpacedPoints


class LinearFunction:
    __slots__ = "a", "b"

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
                print("Stopped from behind (==) at", i + 1, "/", len(values))
                return v
            current_direction = v > y
            if direction is None:
                direction = current_direction
            elif direction is not current_direction:
                print("Stopped from behind (!=) at", i + 1, "/", len(values))
                return v
        raise ValueError(
            f"Unable to get latest intersection {self} from {[self(c) for c in range(n)]} to {y_values}"
        )

    @classmethod
    def get_linear_regression(cls, values: list):
        n = len(values)
        y_values = sorted(values)
        x_values = list(range(n))
        average_x = sum(x_values) / n
        average_y = sum(y_values) / n
        var_x = (sum(x ** 2 for x in x_values) / n) - average_x ** 2
        cov_xy = (
            sum(x * y for x, y in zip(x_values, y_values)) / n
        ) - average_x * average_y
        a = cov_xy / var_x
        b = average_y - a * average_x
        return LinearFunction(a, b)

    @classmethod
    def get_line(cls, x1, y1, x2, y2):
        a = (y2 - y1) / (x2 - x1)
        b = y1 - a * x1
        return LinearFunction(a, b)


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
        return cls.moderate(
            abs(p1.r[index_p1] - p2.r[index_p2])
            + abs(p1.g[index_p1] - p2.g[index_p2])
            + abs(p1.b[index_p1] - p2.b[index_p2])
        )

    @classmethod
    def macro_pixel_distance(cls, p1, x, y, p2, local_x, local_y, width):
        return cls.pixel_distance(p1, x + y * width, p2, local_x + local_y * width)

    @classmethod
    def compare_basic(
        cls,
        p1: Miniature,
        p2: Miniature,
        width: int,
        height: int,
        maximum_similarity_score: Union[int, float],
    ):
        # total_distance = sum(abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2) for (r1, g1, b1), (r2, g2, b2) in zip(p1.data(), p2.data()))
        total_distance = (
            sum(abs(r1 - r2) for r1, r2 in zip(p1.r, p2.r))
            + sum(abs(g1 - g2) for g1, g2 in zip(p1.g, p2.g))
            + sum(abs(b1 - b2) for b1, b2 in zip(p1.b, p2.b))
        )
        return (maximum_similarity_score - total_distance) / maximum_similarity_score

    @classmethod
    def compare_better(
        cls,
        p1: Miniature,
        p2: Miniature,
        width: int,
        height: int,
        maximum_similarity_score: Union[int, float],
    ):
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
                cls.macro_pixel_distance(p1, 0, 0, p2, 1, 1, width),
            )
            + min(  # width - 1, 0
                cls.macro_pixel_distance(p1, width - 1, 0, p2, width - 2, 0, width),
                cls.macro_pixel_distance(p1, width - 1, 0, p2, width - 1, 0, width),
                cls.macro_pixel_distance(p1, width - 1, 0, p2, width - 2, 1, width),
                cls.macro_pixel_distance(p1, width - 1, 0, p2, width - 1, 1, width),
            )
            + min(  # 0, height - 1
                cls.macro_pixel_distance(p1, 0, height - 1, p2, 0, height - 1, width),
                cls.macro_pixel_distance(p1, 0, height - 1, p2, 1, height - 1, width),
                cls.macro_pixel_distance(p1, 0, height - 1, p2, 0, height - 2, width),
                cls.macro_pixel_distance(p1, 0, height - 1, p2, 1, height - 2, width),
            )
            + min(  # width - 1, height - 1
                cls.macro_pixel_distance(
                    p1, width - 1, height - 1, p2, width - 2, height - 1, width
                ),
                cls.macro_pixel_distance(
                    p1, width - 1, height - 1, p2, width - 1, height - 1, width
                ),
                cls.macro_pixel_distance(
                    p1, width - 1, height - 1, p2, width - 2, height - 2, width
                ),
                cls.macro_pixel_distance(
                    p1, width - 1, height - 1, p2, width - 1, height - 2, width
                ),
            )
        )
        for x in range(1, width - 1):
            # x, 0
            total_distance += min(
                cls.macro_pixel_distance(p1, x, 0, p2, x - 1, 0, width),
                cls.macro_pixel_distance(p1, x, 0, p2, x, 0, width),
                cls.macro_pixel_distance(p1, x, 0, p2, x + 1, 0, width),
                cls.macro_pixel_distance(p1, x, 0, p2, x - 1, 1, width),
                cls.macro_pixel_distance(p1, x, 0, p2, x, 1, width),
                cls.macro_pixel_distance(p1, x, 0, p2, x + 1, 1, width),
            )
            # x, height - 1
            total_distance += min(
                cls.macro_pixel_distance(
                    p1, x, height - 1, p2, x - 1, height - 1, width
                ),
                cls.macro_pixel_distance(p1, x, height - 1, p2, x, height - 1, width),
                cls.macro_pixel_distance(
                    p1, x, height - 1, p2, x + 1, height - 1, width
                ),
                cls.macro_pixel_distance(
                    p1, x, height - 1, p2, x - 1, height - 2, width
                ),
                cls.macro_pixel_distance(p1, x, height - 1, p2, x, height - 2, width),
                cls.macro_pixel_distance(
                    p1, x, height - 1, p2, x + 1, height - 2, width
                ),
            )
        for y in range(1, height - 1):
            # 0, y
            total_distance += min(
                cls.macro_pixel_distance(p1, 0, y, p2, 0, y - 1, width),
                cls.macro_pixel_distance(p1, 0, y, p2, 1, y - 1, width),
                cls.macro_pixel_distance(p1, 0, y, p2, 0, y, width),
                cls.macro_pixel_distance(p1, 0, y, p2, 1, y, width),
                cls.macro_pixel_distance(p1, 0, y, p2, 0, y + 1, width),
                cls.macro_pixel_distance(p1, 0, y, p2, 1, y + 1, width),
            )
            # width - 1, y
            total_distance += min(
                cls.macro_pixel_distance(p1, width - 1, y, p2, width - 2, y - 1, width),
                cls.macro_pixel_distance(p1, width - 1, y, p2, width - 1, y - 1, width),
                cls.macro_pixel_distance(p1, width - 1, y, p2, width - 2, y, width),
                cls.macro_pixel_distance(p1, width - 1, y, p2, width - 1, y, width),
                cls.macro_pixel_distance(p1, width - 1, y, p2, width - 2, y + 1, width),
                cls.macro_pixel_distance(p1, width - 1, y, p2, width - 1, y + 1, width),
            )
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
                cls.macro_pixel_distance(p1, x, y, p2, x + 1, y + 1, width),
            )
        return (maximum_similarity_score - total_distance) / maximum_similarity_score


def main():
    for l in (32, 64, 128, 256, 1024 - 4 + 1, 1024):
        pt_to_il = SpacedPoints.available_points_and_spaces(l)
        print(f"Length {l}:")
        for pt, il in sorted(pt_to_il.items()):
            print(f"\t{pt}: {il}")


if __name__ == "__main__":
    main()
