from pysaurus.core.functions import get_percent
from wip.adnoide.adnoide import Life
from wip.adnoide.birth import ControlledNursery, FreeNursery
from wip.adnoide.dna_errors import DNAError, ProteinArgsError, ProteinError
from wip.adnoide.mutation import Individual, Mutagenesis
from wip.adnoide.selection import NaturalSelection, Survival


def create_population(life: Life, count: int, nb_args: int = None) -> list[Individual]:
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


def main():
    # seed = 12345
    seed = 3744358519438480738
    population_size = 1000
    selection_size = population_size // 10
    nb_generations = 1000

    life = Life(seed)
    print("[seed]", life.seed)

    mutagenesis = Mutagenesis(life)
    free_nursery = FreeNursery(mutagenesis, population_size)
    controlled_nursery = ControlledNursery.priority(
        mutagenesis, population_size, selection_size
    )
    nursery = controlled_nursery

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

        survival: list[Survival] = []
        for individual in people:
            try:
                survival.append(nature.survive(individual))
            except (
                ProteinError,
                ValueError,
                ZeroDivisionError,
                OverflowError,
                MemoryError,
            ):
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

        survivants: list[Individual] = [
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
    print("[seed]", life.seed)


def debug_evolution(individual: Individual):
    for i, event in enumerate(individual.get_evolution()):
        print(f"<Generation {i + 1}>")
        print(event)


if __name__ == "__main__":
    # distribute_quantity(900, 100)
    main()
