from ctypes import c_int
from typing import Any, List

import math

from pysaurus.core.video_raptor.structures import Sequence, c_int_p

ALPHABET_SIZE = 256
NB_DIVISIONS = 3
NB_ALPHABET_CLASSES = NB_DIVISIONS + 1
MAX_ALPHABET_VALUE = ALPHABET_SIZE - 1
ALPHABET_CLASS_SIZE = int((ALPHABET_SIZE - 1) // NB_DIVISIONS)
assert ALPHABET_SIZE == NB_DIVISIONS * ALPHABET_CLASS_SIZE + 1


def classify_intensity(value, alphabet_size, divisions):
    n = ((alphabet_size - 1) // divisions) - 1
    if value % (n + 1) == 0:
        c = value
    else:
        i = int(value / (n + 1))
        p1 = i * (n + 1)
        p2 = (i + 1) * (n + 1)
        d1 = value - p1
        d2 = p2 - value
        if d1 <= d2:
            c = p1
        else:
            c = p2
    return c


class IntensityPoint:
    __slots__ = ('value', 'count', 'x', 'y')

    def __init__(self, value):
        # type: (int) -> None
        self.value = value
        self.count = 0
        self.x = 0
        self.y = 0

    def __str__(self):
        return 'IP[%d, n=%d, pos=(%s; %s)]' % (self.value, self.count, self.x, self.y)

    def __hash__(self):
        return hash((self.value, self.count, self.x, self.y))

    def __eq__(self, other):
        # type: (IntensityPoint) -> bool
        return (self.value == other.value
                and self.count == other.count
                and self.x == other.x
                and self.y == other.y)

    def __lt__(self, other):
        # type: (IntensityPoint) -> bool
        return self.value < other.value

    @staticmethod
    def classify(value):
        return classify_intensity(value, ALPHABET_SIZE, NB_DIVISIONS)

    @staticmethod
    def align_points(sequence_1, sequence_2, width, height):
        # type: (List[IntensityPoint], List[IntensityPoint], int, int) -> float
        max_c = ALPHABET_SIZE - 1
        max_n = width * height
        max_d = math.sqrt((width - 1) ** 2 + (height - 1) ** 2)
        class_size = int((ALPHABET_SIZE - 1) // NB_DIVISIONS)
        classes_1 = {ip.value: ip for ip in sequence_1}
        classes_2 = {ip.value: ip for ip in sequence_2}
        score = 0
        nb_classes = 0
        class_value = 0
        while class_value < ALPHABET_SIZE:
            nb_classes += 1
            gg1 = classes_1.get(class_value, None)  # type: IntensityPoint
            gg2 = classes_2.get(class_value, None)  # type: IntensityPoint
            class_value += class_size
            if not gg1 and not gg2:
                continue
            if not gg1:
                gg1 = IntensityPoint(gg2.value)
                gg1.x = gg2.x
                gg1.y = gg2.y
            elif not gg2:
                gg2 = IntensityPoint(gg1.value)
                gg2.x = gg1.x
                gg2.y = gg1.y
            c = abs(gg1.value - gg2.value)
            n = abs(gg1.count - gg2.count)
            d = math.sqrt((gg1.x - gg2.x) ** 2 + (gg1.y - gg2.y) ** 2)
            score += math.sqrt(((max_c - c) / max_c) * ((max_n - n) / max_n) * ((max_d - d) / max_d))
        assert class_value - class_size == ALPHABET_SIZE - 1
        assert nb_classes == NB_DIVISIONS + 1
        return score / nb_classes


class IntensityPointsAligner:
    def __init__(self, width, height):
        # type: (int, int) -> None
        self.max_n = width * height
        self.max_d = math.sqrt((width - 1) ** 2 + (height - 1) ** 2)

    def align_points(self, sequence_1, sequence_2):
        # type: (List[IntensityPoint], List[IntensityPoint]) -> float
        classes_1 = {ip.value: ip for ip in sequence_1}
        classes_2 = {ip.value: ip for ip in sequence_2}
        score = 0
        class_value = 0
        while class_value < ALPHABET_SIZE:
            gg1 = classes_1.get(class_value, None)  # type: IntensityPoint
            gg2 = classes_2.get(class_value, None)  # type: IntensityPoint
            class_value += ALPHABET_CLASS_SIZE
            if not gg1 and not gg2:
                continue
            if not gg1:
                gg1 = IntensityPoint(gg2.value)
                gg1.x = gg2.x
                gg1.y = gg2.y
            elif not gg2:
                gg2 = IntensityPoint(gg1.value)
                gg2.x = gg1.x
                gg2.y = gg1.y
            c = abs(gg1.value - gg2.value)
            n = abs(gg1.count - gg2.count)
            d = math.sqrt((gg1.x - gg2.x) ** 2 + (gg1.y - gg2.y) ** 2)
            score += math.sqrt(
                ((MAX_ALPHABET_VALUE - c) / MAX_ALPHABET_VALUE) *
                ((self.max_n - n) / self.max_n) *
                ((self.max_d - d) / self.max_d)
            )
        return score / NB_ALPHABET_CLASSES


class Miniature:
    __slots__ = ('identifier', 'r', 'g', 'b', 'i', 'width', 'height')

    def __init__(self, red, green, blue, width, height, identifier=None):
        # type: (List[int], List[int], List[int], int, int, Any) -> None
        self.r = red
        self.g = green
        self.b = blue
        self.i = [int(sum(pixel) / 3) for pixel in zip(red, green, blue)]
        self.width = width
        self.height = height
        self.identifier = identifier

    def average_gray_diff(self, other):
        # type: (Miniature) -> float
        nb_values = len(self.i)
        assert len(other.i) == nb_values
        return sum(self.i[index] - other.i[index] for index in range(nb_values)) / nb_values

    def to_intensity_points(self):
        # type: () -> List[IntensityPoint]
        classifiers = {}
        for index, color in enumerate(self.i):
            color = IntensityPoint.classify(color)
            if color in classifiers:
                intensity_point = classifiers[color]
            else:
                intensity_point = IntensityPoint(color)
                classifiers[color] = intensity_point
            intensity_point.count += 1
            intensity_point.x += (index % self.width)
            intensity_point.y += int(index // self.width)
        intensity_points = []
        for intensity_point in classifiers.values():
            intensity_point.x /= intensity_point.count
            intensity_point.y /= intensity_point.count
            intensity_points.append(intensity_point)
        intensity_points.sort()
        return intensity_points

    def to_c_sequence(self):
        array_type = c_int * len(self.r)
        return Sequence(c_int_p(array_type(*self.r)),
                        c_int_p(array_type(*self.g)),
                        c_int_p(array_type(*self.b)),
                        c_int_p(array_type(*self.i)),
                        0.0, 0)
