from ctypes import c_bool

from pysaurus.imgsimsearch.backend_numpy import (
    classify_similarities_directed as f_np,
    shift_bottom,
    shift_bottom_left,
    shift_bottom_right,
    shift_center,
    shift_left,
    shift_right,
    shift_top,
    shift_top_left,
    shift_top_right,
)
from other.legacy.pysaurus.video_similarities import (
    classify_similarities_directed as f_cpp,
    classify_similarities_directed as f_py,
)
from pysaurus.core.miniature import Miniature
from pysaurus.core.notifying import DEFAULT_NOTIFIER


def main():
    w = 6
    h = 7
    r = bytearray(range(w * h))
    g = bytearray(range(w * h, 2 * w * h))
    b = bytearray(range(2 * w * h, 3 * w * h))
    a1 = Miniature(r, g, b, w, h)
    a2 = Miniature(g, b, r, w, h)
    a3 = Miniature(b, r, g, w, h)
    a4 = Miniature(r, b, g, w, h)
    a5 = Miniature(g, b, g, w, h)
    miniatures = [a1, a2, a3, a4, a5]
    edges_cpp = (c_bool * (len(miniatures) * len(miniatures)))()
    for i in range(len(miniatures) * len(miniatures)):
        edges_cpp[i] = 1
    edges_py = [1] * (len(miniatures) * len(miniatures))
    edges_np = [1] * (len(miniatures) * len(miniatures))
    limit = 0.9
    notifier = DEFAULT_NOTIFIER

    f_cpp(miniatures, edges_cpp, limit, notifier)
    f_py(miniatures, edges_py, limit, notifier)
    f_np(miniatures, edges_np, limit, notifier)

    edges_cpp_out = [
        int(edges_cpp[i]) for i in range(len(miniatures) * len(miniatures))
    ]

    if (1 / 2) == 0:
        p = a1.to_numpy()
        print(shift_top_left(p.r))
        print(shift_top(p.r))
        print(shift_top_right(p.r))
        print(shift_left(p.r))
        print(shift_center(p.r))
        print(shift_right(p.r))
        print(shift_bottom_left(p.r))
        print(shift_bottom(p.r))
        print(shift_bottom_right(p.r))

    print(edges_cpp_out)
    print(edges_py)
    print(edges_np)

    assert edges_cpp_out == edges_py
    assert edges_cpp_out == edges_np


if __name__ == "__main__":
    main()
