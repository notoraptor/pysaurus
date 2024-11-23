import inspect
from dataclasses import dataclass
from typing import List, Sequence

from wip.adnoide.adnoide import Life, Protein
from wip.adnoide.dna_errors import DNAError, ProteinArgsError, ProteinError
from wip.adnoide.mutation import Lineage, Mutagenesis


def generate_proteins(life: Life, nb_proteins: int, nb_args: int) -> List[Protein]:
    proteins = []
    for i in range(nb_proteins):
        step = 0
        while True:
            step += 1
            try:
                protein = life.random_protein()
                if protein.nb_inputs != nb_args:
                    raise ProteinArgsError(nb_args, protein.nb_inputs)
                proteins.append(protein)
                print(f"[protein {i + 1}/{nb_proteins}][step {step}] success")
                break
            except DNAError:
                pass
    return proteins


@dataclass(slots=True)
class Selected:
    lineage: Lineage
    distance: float


class NaturalSelection:
    __slots__ = ("_inputs", "_outputs")

    def __init__(self, inputs: Sequence, outputs: Sequence[float]):
        assert len(inputs) == len(outputs)
        self._inputs = [
            inp if isinstance(inp, (list, tuple)) else (inp,) for inp in inputs
        ]
        self._outputs = outputs

    @classmethod
    def from_function(cls, function: callable, inputs: Sequence):
        sig = inspect.signature(function)
        for parameter in sig.parameters.values():
            assert parameter.kind not in (
                parameter.VAR_POSITIONAL,
                parameter.KEYWORD_ONLY,
                parameter.VAR_KEYWORD,
            )
        nb_args = len(sig.parameters)
        formatted_inputs = []
        outputs = []
        for inp in inputs:
            if not isinstance(inp, (list, tuple)):
                assert nb_args == 1
                inp = (inp,)
            formatted_inputs.append(inp)
            outputs.append(function(*inp))
        return cls(formatted_inputs, outputs)

    def stress(self, lineage: Lineage) -> Selected:
        protein = lineage.current_protein()
        distance = sum(
            abs(expected_y - protein(*args))
            for args, expected_y in zip(self._inputs, self._outputs)
        ) / len(self._inputs)
        return Selected(lineage=lineage, distance=distance)

    def debug(self, protein: Protein):
        for args, expected in zip(self._inputs, self._outputs):
            given = protein(*args)
            print(f"f({', '.join(str(x) for x in args)}) = {expected}")
            if expected != given:
                print("\tgot:", given)


def main():
    seed = 12345
    # seed = None
    nb_orig_proteins = 1000
    limit = nb_orig_proteins // 10
    nb_protein_args = 1
    nb_generations = 1000

    life = Life(seed)
    mutagenesis = Mutagenesis(life)
    _proteins = generate_proteins(life, nb_orig_proteins, nb_protein_args)
    lineages = [Lineage(protein) for protein in _proteins]

    nature = NaturalSelection(
        inputs=[1, 2, 5, 7, 11, 20], outputs=[-1, 100, 33, 10, 67, 35]
    )
    nature = NaturalSelection(
        inputs=[(10**i,) for i in range(10)], outputs=[i + 1 for i in range(10)]
    )

    for id_gen in range(nb_generations):
        print(f"[generation {id_gen + 1} / {nb_generations}]")
        print(f"\tpopulation: {len(lineages)}")
        selection = []
        for lineage in lineages:
            try:
                selection.append(nature.stress(lineage))
            except (ProteinError, ValueError, ZeroDivisionError, OverflowError):
                pass
        if not selection:
            print(f"\textinction.")
            break
        print(f"\tsurvive:", len(selection))

        selection.sort(key=lambda sel: (sel.distance, len(sel.lineage.current_gene())))
        best_distance = selection[0].distance
        print(f"\tbest:", best_distance)

        survivants: List[Lineage] = [
            sel.lineage for sel in selection[: min(limit, len(selection))]
        ]
        if best_distance == 0:
            lineages = survivants
            print("\toptimum")
            break

        descendants = []
        nb_children = nb_orig_proteins - len(survivants)
        for i in range(nb_children):
            survivant = survivants[i % len(survivants)]
            derived = mutagenesis.diverge(survivant)
            descendants.append(derived)
        lineages = survivants + descendants

    print()
    print("Best:")
    protein = lineages[0].current_protein()
    print(protein)
    nature.debug(protein)


if __name__ == "__main__":
    main()
