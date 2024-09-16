from enum import Enum
from typing import Any, Dict, List, Sequence, Set

from tqdm import tqdm

from other.imgsimsearchother.native_fine_comparator import compare_images_native
from other.legacy.pysaurus.database.video_similarities.backend_numpy import (
    SimilarityComparator,
)
from pysaurus.core.graph import Graph
from pysaurus.core.miniature import NumpyMiniature
from pysaurus.core.modules import ImageUtils
from pysaurus.imgsimsearch.abstract_image_provider import AbstractImageProvider
from pysaurus.imgsimsearch.common import SIM_LIMIT


class Approximation(Enum):
    ANNOY = "annoy"
    NMSLIB = "nmslib"


def numpy_miniature_from_image(thumbnail, identifier=None) -> NumpyMiniature:
    width, height = thumbnail.size
    size = width * height
    red = bytearray(size)
    green = bytearray(size)
    blue = bytearray(size)
    for i, (r, g, b) in enumerate(thumbnail.getdata()):
        red[i] = r
        green[i] = g
        blue[i] = b
    return NumpyMiniature(red, green, blue, width, height, identifier)


def search_similar_images(
    imp: AbstractImageProvider, approximation: Approximation = Approximation.ANNOY
):
    if approximation == Approximation.ANNOY:
        from pysaurus.imgsimsearch.approximate_comparator_annoy import (
            ApproximateComparatorAnnoy as ApproximateComparator,
        )
    else:
        from other.imgsimsearchother.approximate_comparator import ApproximateComparator
    ac = ApproximateComparator(imp)

    approx_cos = ac.get_comparable_images_cos()
    approx_euc = ac.get_comparable_images_euc()

    all_filenames = sorted(set(approx_cos) | set(approx_euc))
    approx_combined = {
        filename: sorted(
            set(approx_cos.get(filename, ())) & set(approx_euc.get(filename, ()))
        )
        for filename in all_filenames
    }

    return compare_images_native(imp, approx_combined)


def compare_images_python(
    imp: AbstractImageProvider, output: Dict[Any, Sequence[Any]]
) -> List[Set[Any]]:
    nb_images = imp.count()
    numpy_miniatures = {}
    with tqdm(total=nb_images, desc="Generate numpy miniatures") as pbar:
        for identifier, image in imp.items():
            numpy_miniatures[identifier] = numpy_miniature_from_image(
                image.resize(ImageUtils.THUMBNAIL_SIZE)
            )
            pbar.update(1)
    assert len(numpy_miniatures) == nb_images

    graph = Graph()
    nb_todo = sum(len(d) for d in output.values())
    sim_cmp = SimilarityComparator(
        SIM_LIMIT, ImageUtils.THUMBNAIL_DIMENSION, ImageUtils.THUMBNAIL_DIMENSION
    )
    with tqdm(total=nb_todo, desc="Make real comparisons using Numpy") as bar:
        for filename, linked_filenames in output.items():
            p1 = numpy_miniatures[filename]
            for linked_filename in linked_filenames:
                p2 = numpy_miniatures[linked_filename]
                if sim_cmp.are_similar(p1, p2):
                    graph.connect(filename, linked_filename)
                bar.update(1)

    groups = [group for group in graph.pop_groups() if len(group) > 1]
    return groups
