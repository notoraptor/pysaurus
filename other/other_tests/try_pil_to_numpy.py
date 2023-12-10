import sys
from ctypes import pointer

import numpy as np
from PIL import Image

from pysaurus.core.profiling import Profiler
from pysaurus.database.video_similarities.alignment_raptor.alignment import (
    miniature_to_c_sequence,
)
from pysaurus.database.video_similarities.alignment_raptor.symbols import (
    fn_compareSimilarSequences,
)
from pysaurus.database.video_similarities.backend_numba import (
    compare_faster as compare_numba,
)
from pysaurus.database.video_similarities.backend_numba_numpy import (
    compare_faster as compare_numba_numpy,
)
from pysaurus.database.video_similarities.backend_numpy import compare_faster
from pysaurus.database.video_similarities.backend_python import (
    compare_faster as compare_python,
)
from pysaurus.miniature.miniature import Miniature, NumpyMiniature


def miniature_to_numba(m: Miniature):
    from numba.typed import List

    r = List()
    for v in m.r:
        r.append(v)
    g = List()
    for v in m.g:
        g.append(v)
    b = List()
    for v in m.b:
        b.append(v)
    o = List()
    o.append(r)
    o.append(g)
    o.append(b)
    return o


def main():
    w = 32
    h = 32
    s = (w, h)
    image = Image.new("RGB", s, color=(255, 255, 0))
    image2 = Image.new("RGB", s, color=(255, 255, 255))
    r, g, b = image.split()
    # print(set(r.tobytes()))
    # print(set(g.tobytes()))
    # print(set(b.tobytes()))

    # n_r = np.asarray(r, dtype=np.float32)
    # n_g = np.asarray(g, dtype=np.float32)
    # n_b = np.asarray(b, dtype=np.float32)
    # print(n_r.shape, n_g.shape, n_b.shape, file=sys.stderr)
    # print(n_r, file=sys.stderr)
    # print(n_g, file=sys.stderr)
    # print(n_b, file=sys.stderr)

    n1 = NumpyMiniature.from_image(image)
    n2 = NumpyMiniature.from_image(image2)
    m1 = Miniature.from_image(image)
    m2 = Miniature.from_image(image2)
    t1 = np.asarray([n1.r.flatten(), n1.g.flatten(), n1.b.flatten()])
    t2 = np.asarray([n2.r.flatten(), n2.g.flatten(), n2.b.flatten()])
    # print(t1.shape, t1.dtype, t2.shape, t2.dtype, file=sys.stderr)

    r1 = np.asarray([n1.r, n1.g, n1.b])
    r2 = np.asarray([n2.r, n2.g, n2.b])
    # print(t1.shape, t1.dtype, t2.shape, t2.dtype, file=sys.stderr)

    s1 = miniature_to_c_sequence(m1)
    s2 = miniature_to_c_sequence(m2)
    ss1 = pointer(s1)
    ss2 = pointer(s2)

    # t1 = [list(m1.r), list(m1.g), list(m1.b)]
    # t2 = [list(m2.r), list(m2.g), list(m2.b)]

    # t1 = miniature_to_numba(m1)
    # t2 = miniature_to_numba(m2)

    # print(np_dst(n1, n2), file=sys.stderr)

    mds = 255 * 3 * w * h
    batch = 20_000

    with Profiler("Native C++"):
        for _ in range(batch):
            c = fn_compareSimilarSequences(ss1, ss2, w, h, mds)
    print(c, file=sys.stderr)

    with Profiler("Numba"):
        for _ in range(batch):
            c = compare_numba(t1, t2, w, h, mds)
    print(c, file=sys.stderr)

    with Profiler("Numpy"):
        for _ in range(batch):
            c = compare_faster(n1, n2, mds)
    print(c, file=sys.stderr)

    with Profiler("Numba_numpy"):
        for _ in range(batch):
            c = compare_numba_numpy(r1, r2, mds)
    print(c, file=sys.stderr)

    return

    with Profiler("Python"):
        for _ in range(batch):
            c = compare_python(m1, m2, w, h, mds)
    print(c, file=sys.stderr)


if __name__ == "__main__":
    main()
