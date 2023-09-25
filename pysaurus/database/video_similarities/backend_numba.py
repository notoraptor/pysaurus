from numba import njit
from numba.typed import List

Miniature = List
R, G, B = (0, 1, 2)

SIMPLE_MAX_PIXEL_DISTANCE = 255 * 3
V = SIMPLE_MAX_PIXEL_DISTANCE
B = V / 2.0
V_PLUS_B = V + B


@njit
def compare_faster(
    p1: Miniature, p2: Miniature, width: int, height: int, maximum_distance_score: int
):
    # x, y:
    # 0, 0
    total_distance = min(
        pixel_distance(p1, 0, 0, p2, 0, 0, width),
        pixel_distance(p1, 0, 0, p2, 1, 0, width),
        pixel_distance(p1, 0, 0, p2, 0, 1, width),
        pixel_distance(p1, 0, 0, p2, 1, 1, width),
    )
    # width - 1, 0
    total_distance += min(
        pixel_distance(p1, width - 1, 0, p2, width - 2, 0, width),
        pixel_distance(p1, width - 1, 0, p2, width - 1, 0, width),
        pixel_distance(p1, width - 1, 0, p2, width - 2, 1, width),
        pixel_distance(p1, width - 1, 0, p2, width - 1, 1, width),
    )
    # 0, height - 1
    total_distance += min(
        pixel_distance(p1, 0, height - 1, p2, 0, height - 1, width),
        pixel_distance(p1, 0, height - 1, p2, 1, height - 1, width),
        pixel_distance(p1, 0, height - 1, p2, 0, height - 2, width),
        pixel_distance(p1, 0, height - 1, p2, 1, height - 2, width),
    )
    # width - 1, height - 1
    total_distance += min(
        pixel_distance(p1, width - 1, height - 1, p2, width - 2, height - 1, width),
        pixel_distance(p1, width - 1, height - 1, p2, width - 1, height - 1, width),
        pixel_distance(p1, width - 1, height - 1, p2, width - 2, height - 2, width),
        pixel_distance(p1, width - 1, height - 1, p2, width - 1, height - 2, width),
    )
    # x, 0
    for x in range(1, width - 1):
        total_distance += min(
            pixel_distance(p1, x, 0, p2, x - 1, 0, width),
            pixel_distance(p1, x, 0, p2, x, 0, width),
            pixel_distance(p1, x, 0, p2, x + 1, 0, width),
            pixel_distance(p1, x, 0, p2, x - 1, 1, width),
            pixel_distance(p1, x, 0, p2, x, 1, width),
            pixel_distance(p1, x, 0, p2, x + 1, 1, width),
        )
    # x, height - 1
    for x in range(1, width - 1):
        total_distance += min(
            pixel_distance(p1, x, height - 1, p2, x - 1, height - 1, width),
            pixel_distance(p1, x, height - 1, p2, x, height - 1, width),
            pixel_distance(p1, x, height - 1, p2, x + 1, height - 1, width),
            pixel_distance(p1, x, height - 1, p2, x - 1, height - 2, width),
            pixel_distance(p1, x, height - 1, p2, x, height - 2, width),
            pixel_distance(p1, x, height - 1, p2, x + 1, height - 2, width),
        )
    for y in range(1, height - 1):
        # 0, y
        total_distance += min(
            pixel_distance(p1, 0, y, p2, 0, y - 1, width),
            pixel_distance(p1, 0, y, p2, 1, y - 1, width),
            pixel_distance(p1, 0, y, p2, 0, y, width),
            pixel_distance(p1, 0, y, p2, 1, y, width),
            pixel_distance(p1, 0, y, p2, 0, y + 1, width),
            pixel_distance(p1, 0, y, p2, 1, y + 1, width),
        )
        # width - 1, y
        total_distance += min(
            pixel_distance(p1, width - 1, y, p2, width - 2, y - 1, width),
            pixel_distance(p1, width - 1, y, p2, width - 1, y - 1, width),
            pixel_distance(p1, width - 1, y, p2, width - 2, y, width),
            pixel_distance(p1, width - 1, y, p2, width - 1, y, width),
            pixel_distance(p1, width - 1, y, p2, width - 2, y + 1, width),
            pixel_distance(p1, width - 1, y, p2, width - 1, y + 1, width),
        )
    # x in [1; width - 2], y in [1; height - 2]
    remaining_size = (width - 2) * (height - 2)
    for index in range(0, remaining_size):
        x = index % (width - 2) + 1
        y = index // (width - 2) + 1
        total_distance += min(
            pixel_distance(p1, x, y, p2, x - 1, y - 1, width),
            pixel_distance(p1, x, y, p2, x, y - 1, width),
            pixel_distance(p1, x, y, p2, x + 1, y - 1, width),
            pixel_distance(p1, x, y, p2, x - 1, y, width),
            pixel_distance(p1, x, y, p2, x, y, width),
            pixel_distance(p1, x, y, p2, x + 1, y, width),
            pixel_distance(p1, x, y, p2, x - 1, y + 1, width),
            pixel_distance(p1, x, y, p2, x, y + 1, width),
            pixel_distance(p1, x, y, p2, x + 1, y + 1, width),
        )
    return (maximum_distance_score - total_distance) / maximum_distance_score


@njit
def pixel_distance(
    p1: Miniature, x: int, y: int, p2: Miniature, local_x: int, local_y: int, width: int
):
    index_p1 = x + y * width
    index_p2 = local_x + local_y * width
    return moderate(
        abs(p1[0][index_p1] - p2[0][index_p2])
        + abs(p1[1][index_p1] - p2[1][index_p2])
        + abs(p1[2][index_p1] - p2[2][index_p2])
    )


@njit
def moderate(x: float):
    return V_PLUS_B * x / (x + B)
