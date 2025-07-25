from typing import Any, Sequence

from pysaurus.core.graph import Graph
from pysaurus.core.informer import Informer
from pysaurus.core.miniature import Miniature, NumpyMiniature
from pysaurus.imgsimsearch.backend_numpy import SimilarityComparator
from pysaurus.imgsimsearch.common import THUMBNAIL_DIMENSION


def compare_miniatures(
    miniatures_list: list[Miniature],
    comparisons: dict[Any, Sequence[Any]],
    sim_limit: float,
) -> list[set[Any]]:
    notifier = Informer.default()

    all_filenames = set(comparisons)
    for filenames in comparisons.values():
        all_filenames.update(filenames)
    miniatures = {m.identifier: m for m in miniatures_list}
    for filename in all_filenames:
        assert filename in miniatures

    numpy_miniatures: dict[str, NumpyMiniature] = {}
    for miniature in notifier.tasks(
        miniatures_list, "Generate NumPy miniatures", len(miniatures_list)
    ):
        numpy_miniatures[miniature.identifier] = miniature.to_numpy()

    assert len(numpy_miniatures) == len(miniatures_list)

    graph = Graph()
    nb_todo = sum(len(d) for d in comparisons.values())
    sim_cmp = SimilarityComparator(sim_limit, THUMBNAIL_DIMENSION, THUMBNAIL_DIMENSION)

    iterable = (
        (filename, linked_filename)
        for filename, linked_filenames in comparisons.items()
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
