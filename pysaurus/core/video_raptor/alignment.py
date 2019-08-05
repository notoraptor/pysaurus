from ctypes import c_int, c_double, pointer, memset, sizeof
from typing import List, Tuple, Iterable
from array import array

from pysaurus.core.video_raptor.alignment_utils import Miniature
from pysaurus.core.video_raptor.functions import (__PtrPtrSequence, __PtrSequence, __fn_batchAlignmentScore,
                                                  __fn_classifySimilarities, c_double_p)
from pysaurus.core.profiling import Profiler
from pysaurus.core.video_raptor.structures import c_int_p


def align_integer_sequences(sequences_1, sequences_2, width, height, min_val, max_val, gap_score):
    line_type = c_int * (width * height)
    return __fn_batchAlignmentScore(
        c_int_p(line_type(*sequences_1)),
        c_int_p(line_type(*sequences_2)),
        height, width, min_val, max_val, gap_score
    )


def classify_similarities(miniatures):
    # type: (List[Miniature]) -> Iterable[float]
    nb_sequences = len(miniatures)
    native_sequences = [sequence.to_c_sequence() for i, sequence in enumerate(miniatures)]
    native_sequence_pointers = [pointer(sequence) for sequence in native_sequences]
    pointer_array_type = __PtrSequence * nb_sequences
    native_edges = (c_double * (nb_sequences * nb_sequences))()
    memset(native_edges, 0, sizeof(native_edges))
    # assert all(s.classification == -1 for s in native_sequences)
    with Profiler('Finding similar images using simpler NATIVE comparison.'):
        __fn_classifySimilarities(__PtrPtrSequence(pointer_array_type(*native_sequence_pointers)),
                                  nb_sequences, miniatures[0].width, miniatures[0].height, native_edges)
    return native_edges
