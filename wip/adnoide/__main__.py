from typing import Callable, Iterable

from wip.adnoide.adnoide import FUNCTIONS, Protein, SequenceGenerator
from wip.adnoide.dna_errors import ConstantProteinError


def find(callback: Callable[[Protein], None]):
    seq_gen = SequenceGenerator(12345)
    iteration = 0
    while True:
        iteration += 1
        # seq = seq_gen.generate_dna()
        try:
            protein = seq_gen.gof()
            print("[sequence]")
            print(protein.sequence)
            print(f"Protein({protein.nb_inputs} args):")
            print(protein)
            callback(protein)
            print(f"[step {iteration}] success")
            break
        except Exception as exc:
            print(f"[step {iteration}]", type(exc).__name__, exc)
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


def f(x):
    return x**2 + x + 1


def find_on_function(function: callable, args: Iterable, expand=False):
    if expand:
        def callback(protein: Protein):
            for tpl in args:
                assert protein.nb_inputs == len(tpl)
                assert function(*tpl) == protein(*tpl)
    else:
        def callback(protein: Protein):
            assert protein.nb_inputs == 1
            for arg in args:
                assert function(arg) == protein(arg)
                print(f"f({arg}) = {function(arg)}")

    find(callback)


def main():
    for i in range(6):
        print(f"f({i}) = {f(i)}")
    find_on_function(lambda x: x + 2, range(10))


if __name__ == "__main__":
    main()
    # find(criterion_no_constant)
    # find(criterion_1_0)
    # debug()
