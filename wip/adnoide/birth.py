from abc import ABC, abstractmethod
from typing import Sequence

from wip.adnoide.mutation import Individual, Mutagenesis


class AbstractNursery(ABC):
    __slots__ = ("mutagenesis",)

    def __init__(self, mutagenesis: Mutagenesis):
        self.mutagenesis = mutagenesis

    @abstractmethod
    def spring(self, parents: Sequence[Individual]) -> list[Individual]:
        raise NotImplementedError()


class FreeNursery(AbstractNursery):
    __slots__ = ("population_size",)

    def __init__(self, mutagenesis: Mutagenesis, population_size: int):
        super().__init__(mutagenesis)
        self.population_size = population_size

    def spring(self, parents: Sequence[Individual]) -> list[Individual]:
        children = []
        nb_children = self.population_size - len(parents)
        for i in range(nb_children):
            survivant = parents[i % len(parents)]
            child = self.mutagenesis.diverge(survivant)
            children.append(child)
        return children


class ControlledNursery(AbstractNursery):
    __slots__ = ("children_sizes",)

    def __init__(self, mutagenesis: Mutagenesis, children_sizes: list[int]):
        super().__init__(mutagenesis)
        self.children_sizes = children_sizes

    @classmethod
    def priority(cls, mut: Mutagenesis, population_size: int, selection_size: int):
        return cls(
            mut,
            degressive_distribution(population_size - selection_size, selection_size),
        )

    def spring(self, parents: Sequence[Individual]) -> list[Individual]:
        children = []
        for survivant, nb_children in zip(parents, self.children_sizes):
            for _ in range(nb_children):
                child = self.mutagenesis.diverge(survivant)
                children.append(child)
        return children


def degressive_distribution(surface: int, side: int) -> list[int]:
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
