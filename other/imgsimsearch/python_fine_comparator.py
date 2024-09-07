from typing import Any, Dict, List, Sequence, Set

from tqdm import tqdm

from other.imgsimsearch.abstract_image_provider import AbstractImageProvider
from other.imgsimsearch.common import SIM_LIMIT, THUMBNAIL_DIMENSION
from other.legacy.pysaurus.database.video_similarities.backend_numpy import (
    SimilarityComparator,
)
from pysaurus.core.informer import Informer
from pysaurus.core.modules import ImageUtils
from pysaurus.miniature.graph import Graph
from pysaurus.miniature.miniature import Miniature, NumpyMiniature


def compare_images(
    imp: AbstractImageProvider, output: Dict[Any, Sequence[Any]]
) -> List[Set[Any]]:
    nb_images = imp.count()
    numpy_miniatures = {}
    with tqdm(total=nb_images, desc="Generate numpy miniatures") as pbar:
        for identifier, image in imp.items():
            numpy_miniatures[identifier] = NumpyMiniature.from_image(
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


def compare_miniatures(
    miniatures_list: List[Miniature], output: Dict[Any, Sequence[Any]]
) -> List[Set[Any]]:
    notifier = Informer.default()

    all_filenames = set(output)
    for filenames in output.values():
        all_filenames.update(filenames)
    miniatures = {m.identifier: m for m in miniatures_list}
    for filename in all_filenames:
        assert filename in miniatures

    numpy_miniatures: Dict[str, NumpyMiniature] = {}
    for miniature in notifier.tasks(
        miniatures_list, "Generate NumPy miniatures", len(miniatures_list)
    ):
        numpy_miniatures[miniature.identifier] = miniature.to_numpy()

    assert len(numpy_miniatures) == len(miniatures_list)

    graph = Graph()
    nb_todo = sum(len(d) for d in output.values())
    sim_cmp = SimilarityComparator(SIM_LIMIT, THUMBNAIL_DIMENSION, THUMBNAIL_DIMENSION)

    iterable = (
        (filename, linked_filename)
        for filename, linked_filenames in output.items()
        for linked_filename in linked_filenames
    )
    for filename, linked_filename in notifier.tasks(
        iterable, "Make real comparisons using NumPy", nb_todo
    ):
        p1 = numpy_miniatures[filename]
        p2 = numpy_miniatures[linked_filename]
        if sim_cmp.are_similar(p1, p2):
            graph.connect(filename, linked_filename)

    groups = [group for group in graph.pop_groups() if len(group) > 1]
    return groups
