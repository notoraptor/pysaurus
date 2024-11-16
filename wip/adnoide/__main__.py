from typing import Callable

from wip.adnoide.adnoide import FUNCTIONS, Protein, SequenceGenerator
from wip.adnoide.dna_errors import ConstantProteinError


def find(callback: Callable[[Protein], None]):
    seq_gen = SequenceGenerator(12345)
    iteration = 0
    while True:
        iteration += 1
        seq = seq_gen.generate_dna()
        try:
            protein = seq_gen.translate_dna(seq)
            print(f"Protein({protein.nb_inputs} args):")
            print(protein)
            protein.node.expect_type()
            callback(protein)
            print(f"[step {iteration}] success")
            break
        except Exception as exc:
            print(f"[step {iteration}, seq len {len(seq)}]", type(exc).__name__, exc)
            continue


def criterion_no_constant(protein: Protein):
    if protein.nb_inputs == 0:
        raise ConstantProteinError(protein())


def criterion_1_0(protein: Protein):
    assert protein.nb_inputs == 1
    assert protein(0) == 1
    assert protein(1) == 0


def debug():
    for function in FUNCTIONS:
        print(function, function.input_types, function.output_type)


if __name__ == "__main__":
    find(criterion_no_constant)
    # find(criterion_1_0)
    # debug()
