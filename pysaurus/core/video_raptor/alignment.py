from _ctypes import pointer
from ctypes import c_int
from typing import Any, List, Tuple

from pysaurus.core.video_raptor.alignment_utils import Miniature
from pysaurus.core.video_raptor.functions import (__PtrPtrSequence, __PtrSequence, __fn_batchAlignmentScore,
                                                  __fn_classifySimilarities)
from pysaurus.core.video_raptor.structures import c_int_p


def align_integer_sequences(sequences_1, sequences_2, width, height, min_val, max_val, gap_score):
    line_type = c_int * (width * height)
    return __fn_batchAlignmentScore(
        c_int_p(line_type(*sequences_1)),
        c_int_p(line_type(*sequences_2)),
        height, width, min_val, max_val, gap_score
    )


def classify_similarities(parameters):
    # type: (Tuple[List[Any], List[Miniature], int, int, int, int, int, float, float]) -> tuple
    identifiers, miniatures, width, height, min_val, max_val, gap_score, sim_limit, diff_limit = parameters
    nb_sequences = len(miniatures)
    size = width * height
    native_sequences = [sequence.to_c_sequence() for sequence in miniatures]
    native_sequence_pointers = [pointer(sequence) for sequence in native_sequences]
    pointer_array_type = __PtrSequence * nb_sequences
    assert all(s.classification == 0 for s in native_sequences)
    nb_similar_found = __fn_classifySimilarities(
        __PtrPtrSequence(pointer_array_type(*native_sequence_pointers)),
        nb_sequences,
        sim_limit,
        diff_limit,
        height,
        width,
        min_val,
        max_val,
        gap_score
    )
    classes = {}
    for index, native_sequence in enumerate(native_sequences):
        classes.setdefault(native_sequence.classification, []).append(index)
    sim_group = classes.pop(0)
    assert nb_similar_found == len(sim_group), (nb_similar_found, len(sim_group))
    sim_groups = [] if len(sim_group) == 1 else [
        [(identifiers[index], native_sequences[index].score) for index in sim_group]]
    alone_indices = []
    new_potential_sim_groups = []
    for group in classes.values():
        if len(group) == 1:
            alone_indices.append(identifiers[group[0]])
        else:
            new_potential_sim_groups.append([identifiers[index] for index in group])
    return sim_groups, new_potential_sim_groups, alone_indices


def main():
    c1 = Miniature([1, 1, 1, 1, 1, 1], [2, 2, 2, 2, 2, 2], [3, 3, 3, 3, 3, 3], 3, 2)
    c2 = Miniature([0, 1, 1, 1, 1, 1], [2, 2, 0, 2, 2, 2], [3, 3, 3, 3, 0, 3], 3, 2)
    r = classify_similarities(([-1, -2], [c1, c2], 3, 2, 0, 255, -1, 0.94, 0.1))
    print(r)


if __name__ == '__main__':
    main()
