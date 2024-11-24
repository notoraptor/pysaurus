import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Sequence

from pysaurus.core.functions import get_percent
from wip.adnoide.adnoide import Life, Protein
from wip.adnoide.dna_errors import DNAError, ProteinArgsError, ProteinError
from wip.adnoide.mutation import Individual, Mutagenesis


def create_population(life: Life, count: int, nb_args: int = None) -> List[Individual]:
    people = []
    total = 0
    for i in range(count):
        step = 0
        while True:
            step += 1
            try:
                protein = life.random_protein()
                if nb_args is not None and protein.nb_inputs != nb_args:
                    raise ProteinArgsError(nb_args, protein.nb_inputs)
                people.append(Individual(protein))
                break
            except DNAError:
                pass
        total += step
    print(f"[proteins] selected {count} from {total} ({get_percent(count, total)} %)")
    return people


@dataclass(slots=True)
class Survival:
    individual: Individual
    instability: float

    @property
    def key(self):
        return self.instability, len(self.individual.gene)

    def __lt__(self, other: "Survival"):
        return self.key < other.key


class NaturalSelection:
    __slots__ = ("_inputs", "_outputs", "_nb_args")

    def __init__(self, inputs: Sequence, outputs: Sequence[float]):
        assert len(inputs) == len(outputs)
        inputs = [inp if isinstance(inp, (list, tuple)) else (inp,) for inp in inputs]
        (self._nb_args,) = {len(inp) for inp in inputs}
        self._inputs = inputs
        self._outputs = outputs

    @property
    def feed_size(self) -> int:
        return self._nb_args

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

    def survive(self, individual: Individual) -> Survival:
        protein = individual.protein
        distance = sum(
            abs(expected_y - protein(*args))
            for args, expected_y in zip(self._inputs, self._outputs)
        ) / len(self._inputs)
        return Survival(individual=individual, instability=distance)

    def debug(self, protein: Protein):
        for args, expected in zip(self._inputs, self._outputs):
            given = protein(*args)
            print(f"f({', '.join(str(x) for x in args)}) = {expected}")
            if expected != given:
                print("\tgot:", given)


def debug_evolution(individual: Individual):
    for i, event in enumerate(individual.get_evolution()):
        print(f"<Generation {i + 1}>")
        print(event)


class AbstractNursery(ABC):
    __slots__ = ("mutagenesis",)

    def __init__(self, mutagenesis: Mutagenesis):
        self.mutagenesis = mutagenesis

    @abstractmethod
    def spring(self, parents: Sequence[Individual]) -> List[Individual]:
        raise NotImplementedError()


class FreeNursery(AbstractNursery):
    __slots__ = ("population_size",)

    def __init__(self, mutagenesis: Mutagenesis, population_size: int):
        super().__init__(mutagenesis)
        self.population_size = population_size

    def spring(self, parents: Sequence[Individual]) -> List[Individual]:
        children = []
        nb_children = self.population_size - len(parents)
        for i in range(nb_children):
            survivant = parents[i % len(parents)]
            child = self.mutagenesis.diverge(survivant)
            children.append(child)
        return children


class ControlledNursery(AbstractNursery):
    __slots__ = ("children_sizes",)

    def __init__(self, mutagenesis: Mutagenesis, children_sizes: List[int]):
        super().__init__(mutagenesis)
        self.children_sizes = children_sizes

    def spring(self, parents: Sequence[Individual]) -> List[Individual]:
        children = []
        for survivant, nb_children in zip(parents, self.children_sizes):
            for _ in range(nb_children):
                child = self.mutagenesis.diverge(survivant)
                children.append(child)
        return children


def distribute_quantity(surface: int, side: int) -> List[int]:
    """
    surface = (1 * side) + (side * other_side / 2)
    surface = side + (side * other_side / 2)
    surface - side = side * other_side / 2
    2 * (surface - side) = side * other_side
    2 * (surface - side) / side = other_side

    f(0) = 0
    f(side - 1) = other_side
    ax+b = c
    a0+b = 0
    b=0
    a(side-1) + b = other_side
    a(side-1) = other_side
    a = other_side / (side - 1)
    """
    other_side = 2 * (surface - side) / side
    a = other_side / (side - 1)
    b = 0
    distribution = [round(a * x + b + 1) for x in reversed(range(side))]
    distributed = sum(distribution)
    remaining = surface - distributed
    assert remaining >= 0
    if remaining > 0:
        distribution[0] += remaining
    return distribution


def main():
    seed = 12345
    # seed = None
    population_size = 1000
    selection_size = population_size // 10
    nb_generations = 1000

    children_sizes = distribute_quantity(population_size - selection_size, selection_size)
    life = Life(seed)
    mutagenesis = Mutagenesis(life)
    free_nursery = FreeNursery(mutagenesis, population_size)
    controlled_nursery = ControlledNursery(mutagenesis, children_sizes)
    nursery = free_nursery

    nature = NaturalSelection(
        inputs=[(10**i,) for i in range(10)], outputs=[i + 1 for i in range(10)]
    )
    nature = NaturalSelection(
        inputs=[1, 2, 5, 7, 11, 20], outputs=[-1, 100, 33, 10, 67, 35]
    )
    people = create_population(life, population_size, nature.feed_size)

    for id_gen in range(nb_generations):
        print(f"[generation {id_gen + 1} / {nb_generations}]")
        print(f"\tpopulation: {len(people)}")
        print(f"\tLongest sequence: {max(len(ind.gene) for ind in people)}")

        survival: List[Survival] = []
        for individual in people:
            try:
                survival.append(nature.survive(individual))
            except (ProteinError, ValueError, ZeroDivisionError, OverflowError, MemoryError):
                pass
            except RuntimeError as exc:
                raise Exception(str(individual.protein)) from exc
        if not survival:
            print(f"\textinction./.")
            break
        print(f"\tsurvive:", len(survival))

        survival.sort()
        best_distance = survival[0].instability
        print(f"\tbest:", best_distance)

        survivants: List[Individual] = [
            srv.individual for srv in survival[: min(selection_size, len(survival))]
        ]

        if best_distance == 0:
            print("\toptimum./.")
            people = survivants
            break
        else:
            children = nursery.spring(survivants)
            print(f"\tchildren: {len(children)}")
            people = survivants + children

    print("\nBest protein:")
    protein = people[0].protein
    print(protein)
    nature.debug(protein)


if __name__ == "__main__":
    # distribute_quantity(900, 100)
    main()
