import numpy as np

from numba import njit

SIMPLE_MAX_PIXEL_DISTANCE = 255 * 3
V = SIMPLE_MAX_PIXEL_DISTANCE
B = V / 2.0
V_PLUS_B = V + B


@njit
def shift_top_left(arr, fill_value=np.inf):
    result = np.empty_like(arr)
    result[0] = fill_value
    result[:, 0] = fill_value
    result[1:, 1:] = arr[:-1, :-1]
    return result


@njit
def shift_top(arr, fill_value=np.inf):
    result = np.empty_like(arr)
    result[0] = fill_value
    result[1:, :] = arr[:-1, :]
    return result


@njit
def shift_top_right(arr, fill_value=np.inf):
    result = np.empty_like(arr)
    result[0] = fill_value
    result[:, -1] = fill_value
    result[1:, :-1] = arr[:-1, 1:]
    return result


@njit
def shift_left(arr, fill_value=np.inf):
    result = np.empty_like(arr)
    result[:, 0] = fill_value
    result[:, 1:] = arr[:, :-1]
    return result


@njit
def shift_center(arr, fill_value=np.inf):
    return arr


@njit
def shift_right(arr, fill_value=np.inf):
    result = np.empty_like(arr)
    result[:, -1] = fill_value
    result[:, :-1] = arr[:, 1:]
    return result


@njit
def shift_bottom_left(arr, fill_value=np.inf):
    result = np.empty_like(arr)
    result[-1] = fill_value
    result[:, 0] = fill_value
    result[:-1, 1:] = arr[1:, :-1]
    return result


@njit
def shift_bottom(arr, fill_value=np.inf):
    result = np.empty_like(arr)
    result[-1] = fill_value
    result[:-1, :] = arr[1:, :]
    return result


@njit
def shift_bottom_right(arr, fill_value=np.inf):
    result = np.empty_like(arr)
    result[-1] = fill_value
    result[:, -1] = fill_value
    result[:-1, :-1] = arr[1:, 1:]
    return result


@njit
def compare_faster(p1: np.ndarray, p2: np.ndarray, maximum_distance_score: int):
    # x, y to x - 1, y - 1
    top_left = RGB(shift_top_left(p2[0]), shift_top_left(p2[1]), shift_top_left(p2[2]))
    # x, y to x, y - 1
    top = RGB(shift_top(p2[0]), shift_top(p2[1]), shift_top(p2[2]))
    # x, y to x + 1, y - 1
    top_right = RGB(
        shift_top_right(p2[0]), shift_top_right(p2[1]), shift_top_right(p2[2])
    )
    # x, y to x - 1, y
    left = RGB(shift_left(p2[0]), shift_left(p2[1]), shift_left(p2[2]))
    # x, y to x, y
    center = RGB(shift_center(p2[0]), shift_center(p2[1]), shift_center(p2[2]))
    # x, y to x + 1, y
    right = RGB(shift_right(p2[0]), shift_right(p2[1]), shift_right(p2[2]))
    # x, y to x - 1, y + 1
    bottom_left = RGB(
        shift_bottom_left(p2[0]), shift_bottom_left(p2[1]), shift_bottom_left(p2[2])
    )
    # x, y to x, y + 1
    bottom = RGB(shift_bottom(p2[0]), shift_bottom(p2[1]), shift_bottom(p2[2]))
    # x, y to x + 1, y + 1
    bottom_right = RGB(
        shift_bottom_right(p2[0]), shift_bottom_right(p2[1]), shift_bottom_right(p2[2])
    )

    total_distance = np.sum(
        np.minimum(
            np_dst(p1, top_left),
            np.minimum(
                np_dst(p1, top),
                np.minimum(
                    np_dst(p1, top_right),
                    np.minimum(
                        np_dst(p1, left),
                        np.minimum(
                            np_dst(p1, center),
                            np.minimum(
                                np_dst(p1, right),
                                np.minimum(
                                    np_dst(p1, bottom_left),
                                    np.minimum(
                                        np_dst(p1, bottom), np_dst(p1, bottom_right)
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
    )
    return (maximum_distance_score - total_distance) / maximum_distance_score


@njit
def RGB(r, g, b):
    return [r, g, b]


@njit
def np_dst(rgb1, rgb2):
    return np.nan_to_num(
        moderate(
            np.abs(rgb1[0] - rgb2[0])
            + np.abs(rgb1[1] - rgb2[1])
            + np.abs(rgb1[2] - rgb2[2])
        ),
        nan=np.inf,
    )


@njit
def moderate(x: float):
    return V_PLUS_B * x / (x + B)
