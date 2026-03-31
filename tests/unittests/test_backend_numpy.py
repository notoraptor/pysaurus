from collections import namedtuple

import numpy as np
import pytest

from pysaurus.core.miniature import NumpyMiniature
from pysaurus.imgsimsearch.backend_numpy import (
    SIMPLE_MAX_PIXEL_DISTANCE,
    SimilarityComparator,
    compare_faster,
    moderate,
    np_dst,
    shift_bottom,
    shift_bottom_left,
    shift_bottom_right,
    shift_left,
    shift_right,
    shift_top,
    shift_top_left,
    shift_top_right,
)


def _make_miniature(
    r: list[list[int]], g: list[list[int]], b: list[list[int]]
) -> NumpyMiniature:
    """Build a NumpyMiniature from 2D lists of pixel values (0-255)."""
    h = len(r)
    w = len(r[0])
    flat_r = bytearray(v for row in r for v in row)
    flat_g = bytearray(v for row in g for v in row)
    flat_b = bytearray(v for row in b for v in row)
    return NumpyMiniature(flat_r, flat_g, flat_b, w, h, identifier=None)


class TestShiftFunctions:
    @pytest.fixture()
    def arr(self):
        return np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=np.float32)

    def test_shift_top_left(self, arr):
        result = shift_top_left(arr)
        assert result[0, 0] == np.inf
        assert result[0, 1] == np.inf
        assert result[1, 0] == np.inf
        assert result[1, 1] == 1
        assert result[2, 2] == 5

    def test_shift_top(self, arr):
        result = shift_top(arr)
        np.testing.assert_array_equal(result[0], [np.inf, np.inf, np.inf])
        np.testing.assert_array_equal(result[1], [1, 2, 3])
        np.testing.assert_array_equal(result[2], [4, 5, 6])

    def test_shift_top_right(self, arr):
        result = shift_top_right(arr)
        assert result[0, 0] == np.inf
        assert result[1, 2] == np.inf
        assert result[1, 0] == 2
        assert result[2, 1] == 6

    def test_shift_left(self, arr):
        result = shift_left(arr)
        assert result[0, 0] == np.inf
        assert result[1, 0] == np.inf
        assert result[0, 1] == 1
        assert result[1, 2] == 5

    def test_shift_right(self, arr):
        result = shift_right(arr)
        assert result[0, 2] == np.inf
        assert result[1, 2] == np.inf
        assert result[0, 0] == 2
        assert result[1, 1] == 6

    def test_shift_bottom_left(self, arr):
        result = shift_bottom_left(arr)
        assert result[2, 0] == np.inf
        assert result[2, 1] == np.inf
        assert result[0, 0] == np.inf
        assert result[0, 1] == 4
        assert result[1, 2] == 8

    def test_shift_bottom(self, arr):
        result = shift_bottom(arr)
        np.testing.assert_array_equal(result[0], [4, 5, 6])
        np.testing.assert_array_equal(result[1], [7, 8, 9])
        np.testing.assert_array_equal(result[2], [np.inf, np.inf, np.inf])

    def test_shift_bottom_right(self, arr):
        result = shift_bottom_right(arr)
        assert result[2, 0] == np.inf
        assert result[0, 2] == np.inf
        assert result[0, 0] == 5
        assert result[1, 1] == 9


class TestModerate:
    def test_zero(self):
        assert moderate(0.0) == 0.0

    def test_positive(self):
        result = moderate(100.0)
        assert result > 0

    def test_monotonic(self):
        values = [moderate(float(x)) for x in range(0, 1000, 10)]
        assert values == sorted(values)


class TestNpDst:
    def test_identical_rgb_returns_zero(self):
        RGB = namedtuple("RGB", ("r", "g", "b"))
        a = RGB(
            np.array([1.0, 2.0], dtype=np.float32),
            np.array([3.0, 4.0], dtype=np.float32),
            np.array([5.0, 6.0], dtype=np.float32),
        )
        result = np_dst(a, a)
        np.testing.assert_array_equal(result, [0.0, 0.0])

    def test_different_rgb(self):
        RGB = namedtuple("RGB", ("r", "g", "b"))
        a = RGB(
            np.array([10.0], dtype=np.float32),
            np.array([20.0], dtype=np.float32),
            np.array([30.0], dtype=np.float32),
        )
        b = RGB(
            np.array([10.0], dtype=np.float32),
            np.array([20.0], dtype=np.float32),
            np.array([30.0], dtype=np.float32),
        )
        assert np_dst(a, b).item() == 0.0


class TestCompareFaster:
    def test_identical_images_return_1(self):
        pixels = [[100, 150], [200, 50]]
        m = _make_miniature(pixels, pixels, pixels)
        mds = SIMPLE_MAX_PIXEL_DISTANCE * 2 * 2
        score = compare_faster(m, m, mds)
        assert score == pytest.approx(1.0)

    def test_different_images_return_less_than_1(self):
        p1 = [[0, 0], [0, 0]]
        p2 = [[255, 255], [255, 255]]
        m1 = _make_miniature(p1, p1, p1)
        m2 = _make_miniature(p2, p2, p2)
        mds = SIMPLE_MAX_PIXEL_DISTANCE * 2 * 2
        score = compare_faster(m1, m2, mds)
        assert score < 1.0

    def test_score_deterministic(self):
        rng = np.random.RandomState(123)
        r1 = rng.randint(0, 256, (4, 4)).tolist()
        r2 = rng.randint(0, 256, (4, 4)).tolist()
        g1 = rng.randint(0, 256, (4, 4)).tolist()
        g2 = rng.randint(0, 256, (4, 4)).tolist()
        b1 = rng.randint(0, 256, (4, 4)).tolist()
        b2 = rng.randint(0, 256, (4, 4)).tolist()
        m1 = _make_miniature(r1, g1, b1)
        m2 = _make_miniature(r2, g2, b2)
        mds = SIMPLE_MAX_PIXEL_DISTANCE * 4 * 4
        assert compare_faster(m1, m2, mds) == pytest.approx(compare_faster(m1, m2, mds))

    def test_score_in_0_1_range(self):
        rng = np.random.RandomState(456)
        r1 = rng.randint(0, 256, (3, 3)).tolist()
        g1 = rng.randint(0, 256, (3, 3)).tolist()
        b1 = rng.randint(0, 256, (3, 3)).tolist()
        r2 = rng.randint(0, 256, (3, 3)).tolist()
        g2 = rng.randint(0, 256, (3, 3)).tolist()
        b2 = rng.randint(0, 256, (3, 3)).tolist()
        m1 = _make_miniature(r1, g1, b1)
        m2 = _make_miniature(r2, g2, b2)
        mds = SIMPLE_MAX_PIXEL_DISTANCE * 3 * 3
        score = compare_faster(m1, m2, mds)
        assert 0.0 <= score <= 1.0

    def test_similar_images_score_higher_than_different(self):
        base = [[100, 110], [120, 130]]
        close = [[101, 111], [121, 131]]
        far = [[0, 0], [0, 0]]
        m_base = _make_miniature(base, base, base)
        m_close = _make_miniature(close, close, close)
        m_far = _make_miniature(far, far, far)
        mds = SIMPLE_MAX_PIXEL_DISTANCE * 2 * 2
        assert compare_faster(m_base, m_close, mds) > compare_faster(m_base, m_far, mds)


class TestSimilarityComparator:
    def test_identical_are_similar(self):
        pixels = [[80, 120, 200], [40, 160, 90]]
        m = _make_miniature(pixels, pixels, pixels)
        cmp = SimilarityComparator(limit=0.9, width=3, height=2)
        assert cmp.are_similar(m, m)

    def test_very_different_not_similar(self):
        black = [[0, 0], [0, 0]]
        white = [[255, 255], [255, 255]]
        m1 = _make_miniature(black, black, black)
        m2 = _make_miniature(white, white, white)
        cmp = SimilarityComparator(limit=0.9, width=2, height=2)
        assert not cmp.are_similar(m1, m2)
