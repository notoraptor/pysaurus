from ctypes import pointer
from typing import Any, Dict, List, Sequence, Set

from other.imgsimsearch.abstract_image_provider import AbstractImageProvider
from other.imgsimsearch.graph import Graph
from pysaurus.core.informer import Informer
from pysaurus.core.profiling import Profiler
from pysaurus.miniature.miniature import Miniature
from pysaurus.video_similarities.alignment_raptor.alignment import (
    miniature_to_c_sequence,
)
from pysaurus.video_similarities.alignment_raptor.symbols import (
    fn_compareSimilarSequences,
)

SIM_LIMIT = 88 / 100
SIMPLE_MAX_PIXEL_DISTANCE = 255 * 3
THUMBNAIL_DIMENSION = 32
THUMBNAIL_SIZE = (THUMBNAIL_DIMENSION, THUMBNAIL_DIMENSION)


class CppSimilarityComparator:
    __slots__ = ("max_dst_score", "limit", "width", "height")

    def __init__(self, limit, width, height):
        self.width = width
        self.height = height
        self.limit = limit
        self.max_dst_score = SIMPLE_MAX_PIXEL_DISTANCE * width * height

    def are_similar(self, p1, p2) -> bool:
        return (
            fn_compareSimilarSequences(
                p1, p2, self.width, self.height, self.max_dst_score
            )
            >= self.limit
        )


def compare_images_native(
    imp: AbstractImageProvider, output: Dict[Any, Sequence[Any]]
) -> List[Set[Any]]:
    all_filenames = set(output)
    for filenames in output.values():
        all_filenames.update(filenames)
    notifier = Informer.default()
    nb_images = imp.count()
    miniatures = {}
    for identifier, image in notifier.tasks(
        imp.items(), desc="Generate miniatures", total=nb_images
    ):
        if identifier in all_filenames:
            miniatures[identifier] = Miniature.from_image(image.resize(THUMBNAIL_SIZE))
    assert len(miniatures) == len(all_filenames)

    with Profiler("Generate native sequences"):
        native_sequences = {
            identifier: miniature_to_c_sequence(sequence)
            for identifier, sequence in miniatures.items()
        }
        native_sequence_pointers = {
            identifier: pointer(sequence)
            for identifier, sequence in native_sequences.items()
        }

    graph = Graph()
    nb_todo = sum(len(d) for d in output.values())
    sim_cmp = CppSimilarityComparator(
        SIM_LIMIT, THUMBNAIL_DIMENSION, THUMBNAIL_DIMENSION
    )

    iterable = (
        (filename, linked_filename)
        for filename, linked_filenames in output.items()
        for linked_filename in linked_filenames
    )
    for filename, linked_filename in notifier.tasks(
        iterable, "Make real comparisons", nb_todo
    ):
        p1 = native_sequence_pointers[filename]
        p2 = native_sequence_pointers[linked_filename]
        if sim_cmp.are_similar(p1, p2):
            graph.connect(filename, linked_filename)

    groups = [group for group in graph.pop_groups() if len(group) > 1]
    return groups


def compare_miniatures_native(
    miniatures_list: List[Miniature], output: Dict[Any, Sequence[Any]]
) -> List[Set[Any]]:
    all_filenames = set(output)
    for filenames in output.values():
        all_filenames.update(filenames)
    notifier = Informer.default()
    miniatures = {m.identifier: m for m in miniatures_list}
    for filename in all_filenames:
        assert filename in miniatures

    with Profiler("Generate native sequences"):
        native_sequences = {
            identifier: miniature_to_c_sequence(sequence)
            for identifier, sequence in miniatures.items()
        }
        native_sequence_pointers = {
            identifier: pointer(sequence)
            for identifier, sequence in native_sequences.items()
        }

    graph = Graph()
    nb_todo = sum(len(d) for d in output.values())
    sim_cmp = CppSimilarityComparator(
        SIM_LIMIT, THUMBNAIL_DIMENSION, THUMBNAIL_DIMENSION
    )

    iterable = (
        (filename, linked_filename)
        for filename, linked_filenames in output.items()
        for linked_filename in linked_filenames
    )
    for filename, linked_filename in notifier.tasks(
        iterable, "Make real comparisons", nb_todo
    ):
        p1 = native_sequence_pointers[filename]
        p2 = native_sequence_pointers[linked_filename]
        if sim_cmp.are_similar(p1, p2):
            graph.connect(filename, linked_filename)

    groups = [group for group in graph.pop_groups() if len(group) > 1]
    return groups
