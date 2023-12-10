from ctypes import pointer
from typing import Any, Dict, List, Sequence, Set

from tqdm import tqdm

from other.imgsimsearch.abstract_image_provider import AbstractImageProvider
from other.imgsimsearch.graph import Graph
from pysaurus.core.profiling import InlineProfiler
from pysaurus.database.video_similarities.alignment_raptor.alignment import (
    miniature_to_c_sequence,
)
from pysaurus.database.video_similarities.alignment_raptor.symbols import (
    fn_compareSimilarSequences,
)
from pysaurus.miniature.miniature import Miniature

SIM_LIMIT = 89 / 100
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
    nb_images = imp.count()
    miniatures = {}
    with tqdm(total=nb_images, desc="Generate numpy miniatures") as pbar:
        for identifier, image in imp.items():
            miniatures[identifier] = Miniature.from_image(image.resize(THUMBNAIL_SIZE))
            pbar.update(1)
    assert len(miniatures) == nb_images

    with InlineProfiler("Generate native sequences"):
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
    with tqdm(total=nb_todo, desc="Make real comparisons using Numpy") as bar:
        for filename, linked_filenames in output.items():
            p1 = native_sequence_pointers[filename]
            for linked_filename in linked_filenames:
                p2 = native_sequence_pointers[linked_filename]
                if sim_cmp.are_similar(p1, p2):
                    graph.connect(filename, linked_filename)
                bar.update(1)

    groups = [group for group in graph.pop_groups() if len(group) > 1]
    return groups
