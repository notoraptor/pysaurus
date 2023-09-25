import numpy as np
from PIL import Image

from pysaurus.database.video_similarities.backend_numpy import compare_faster, np_dst
from pysaurus.database.video_similarities.backend_python import (
    compare_faster as compare_python,
)
from pysaurus.miniature.miniature import Miniature, NumpyMiniature


def main():
    image = Image.new("RGB", (7, 5), color=(255, 255, 0))
    image2 = Image.new("RGB", (7, 5), color=(255, 255, 255))
    r, g, b = image.split()
    n_r = np.asarray(r, dtype=np.float32)
    n_g = np.asarray(g, dtype=np.float32)
    n_b = np.asarray(b, dtype=np.float32)
    print(n_r.shape, n_g.shape, n_b.shape)
    print(n_r)
    print(n_g)
    print(n_b)

    n1 = NumpyMiniature.from_image(image)
    n2 = NumpyMiniature.from_image(image2)
    print(np_dst(n1, n2))
    print(compare_faster(n1, n2, 255 * 3 * 5 * 7))
    print(compare_faster(n2, n1, 255 * 3 * 5 * 7))
    print(
        compare_python(
            Miniature.from_image(image),
            Miniature.from_image(image2),
            7,
            5,
            255 * 3 * 5 * 7,
        )
    )
    print(
        compare_python(
            Miniature.from_image(image2),
            Miniature.from_image(image),
            7,
            5,
            255 * 3 * 5 * 7,
        )
    )


if __name__ == "__main__":
    main()
