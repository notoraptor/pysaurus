from ctypes import c_int, pointer
from typing import List

from pysaurus.core.abstract_notifier import AbstractNotifier
from pysaurus.core.constants import VIDEO_BATCH_SIZE
from pysaurus.core.miniature import Miniature
from pysaurus.core.native.clibrary import c_int_p
from pysaurus.core.profiling import Profiler
from saurus.language import say
from .symbols import (
    PtrPtrSequence,
    PtrSequence,
    Sequence,
    fn_classifySimilaritiesDirected,
)


def miniature_to_c_sequence(self, score=0.0, classification=-1):
    array_type = c_int * len(self.r)
    return Sequence(
        c_int_p(array_type(*self.r)),
        c_int_p(array_type(*self.g)),
        c_int_p(array_type(*self.b)),
        None if self.i is None else c_int_p(array_type(*self.i)),
        score,
        classification,
    )


def classify_similarities_directed(
    miniatures: List[Miniature], edges, sim_limit, notifier: AbstractNotifier
):
    nb_sequences = len(miniatures)
    with Profiler(say("Allocate native data"), notifier):
        native_sequences = [
            miniature_to_c_sequence(sequence) for sequence in miniatures
        ]
        native_sequence_pointers = [pointer(sequence) for sequence in native_sequences]
        pointer_array_type = PtrSequence * nb_sequences
    with Profiler(
        say("Finding similar images using simpler NATIVE comparison."), notifier
    ):
        notifier.task("compare_miniatures", nb_sequences, "videos (C++ comparison)")
        cursor = 0
        while cursor < nb_sequences:
            i_from = cursor
            i_to = cursor + VIDEO_BATCH_SIZE
            fn_classifySimilaritiesDirected(
                PtrPtrSequence(pointer_array_type(*native_sequence_pointers)),
                nb_sequences,
                i_from,
                i_to,
                miniatures[0].width,
                miniatures[0].height,
                edges,
                sim_limit,
            )
            notifier.progress(
                "compare_miniatures", min(i_to, nb_sequences), nb_sequences
            )
            cursor = i_to
        notifier.progress("compare_miniatures", nb_sequences, nb_sequences)
