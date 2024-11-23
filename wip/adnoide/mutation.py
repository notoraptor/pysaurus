import inspect
from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Dict, List, Self, Sequence, Type

from pysaurus.core.classes import StringPrinter
from wip.adnoide.adnoide import Life, Protein
from wip.adnoide.dna_errors import DNAError, ProteinArgsError


class _AbstractSizeable[T](ABC):
    __slots__ = ("life", "min", "max")

    def __init__(self, life: Life, a: int, b: int):
        self.life = life
        self.min = a
        self.max = b

    @classmethod
    @abstractmethod
    def from_life(cls, life: Life, gene: Sequence[int]) -> Self:
        raise NotImplementedError()

    @abstractmethod
    def random(self) -> T:
        raise NotImplementedError()


class _IntegerInterval(_AbstractSizeable[int]):
    __slots__ = ()

    def random(self) -> int:
        return self.life.randint(self.min, self.max)


class ReadingPoint(_IntegerInterval):
    __slots__ = ()

    @classmethod
    def from_life(cls, life: Life, gene: Sequence[int]) -> Self:
        return cls(life, 0, len(gene) - 1)


class WritingPoint(_IntegerInterval):
    __slots__ = ()

    @classmethod
    def from_life(cls, life: Life, gene: Sequence[int]) -> Self:
        return cls(life, 0, len(gene))


class Length(_IntegerInterval):
    __slots__ = ()

    @classmethod
    def from_life(cls, life: Life, gene: Sequence[int]) -> Self:
        return cls(life, 1, len(gene))


class CodonList(_AbstractSizeable[List[int]]):
    __slots__ = ()

    @classmethod
    def from_life(cls, life: Life, gene: Sequence[int]) -> Self:
        return cls(life, life.min_length, life.max_length)

    def random(self) -> List[int]:
        return self.life.random_dna(self.min, self.max)


class MutationMeta(ABCMeta):
    @classmethod
    def _filter(cls, key: str, value):
        return (
            "a" <= key[0] <= "z"
            and inspect.isclass(value)
            and issubclass(value, _AbstractSizeable)
        )

    def __new__(cls, name, bases, namespace: Dict[str, Any]):
        _mkey = "__mutprops__"
        if _mkey not in namespace:
            mutprops = {
                key: value
                for key, value in namespace.items()
                if cls._filter(key, value)
            }
            for key, value in namespace.get("__annotations__", {}).items():
                if cls._filter(key, value):
                    if key in mutprops:
                        assert mutprops[key] is value
                    else:
                        mutprops[key] = value
            namespace[_mkey] = mutprops
        return super().__new__(cls, name, bases, namespace)


class MutationEvent:
    __slots__ = ("name", "parameters", "output", "protein")

    def __init__(
        self, name: str, parameters: dict, output: Sequence[int], protein=None
    ):
        self.name = name
        self.parameters = parameters
        self.output = output
        self.protein = protein

    def __repr__(self):
        with StringPrinter() as printer:
            printer.write(self.name)
            if self.parameters:
                printer.write("\tparameters:")
                for key, value in self.parameters.items():
                    printer.write(f"\t\t{key}: {value}")
            if self.output:
                printer.write("\toutput:")
                printer.write(f"\t\t{self.output}")
            return str(printer)


class Mutation(metaclass=MutationMeta):
    __slots__ = ("life", "gene", "props")

    __mutprops__: Dict[str, Type[_AbstractSizeable]]

    def __init__(self, life: Life, gene: Sequence[int]):
        self.life = life
        self.gene = gene
        self.props: Dict[str, _AbstractSizeable] = {
            name: cls.from_life(life, gene) for name, cls in self.__mutprops__.items()
        }

    def random(self) -> MutationEvent:
        parameters = {name: prop.random() for name, prop in self.props.items()}
        output = self.mutate(**parameters)
        return MutationEvent(type(self).__name__, parameters, output)

    @abstractmethod
    def mutate(self, **kwargs) -> List[int]:
        raise NotImplementedError()


class Substitution(Mutation):
    """replace n codons by m new codons at position p"""

    __slots__ = ()
    position: ReadingPoint
    length: Length
    codons: CodonList

    def mutate(self, position: int, length: int, codons: List[int]) -> List[int]:
        gene = list(self.gene)
        return gene[:position] + codons + gene[position + length :]


class Insertion(Mutation):
    """n new inserted at position p"""

    __slots__ = ()
    position: WritingPoint
    codons: CodonList

    def mutate(self, position: int, codons: List[int]) -> List[int]:
        gene = list(self.gene)
        return gene[:position] + codons + gene[position:]


class Deletion(Mutation):
    """n deleted at position p"""

    __slots__ = ()
    position: ReadingPoint
    length: Length

    def mutate(self, position: int, length: int) -> List[int]:
        gene = list(self.gene)
        return gene[:position] + gene[position + length :]


class Duplication(Mutation):
    """duplication: n copied from position p1 at position p2"""

    __slots__ = ()
    from_position: ReadingPoint
    to_position: ReadingPoint
    length: Length

    def mutate(self, from_position: int, to_position: int, length: int) -> List[int]:
        gene = list(self.gene)
        codons = gene[from_position : from_position + length]
        return gene[:to_position] + codons + gene[to_position:]


class Lineage:
    __slots__ = ("_generations", "_origin")

    def __init__(self, protein: Protein, origin: "Lineage" = None):
        self._generations: List[MutationEvent] = [
            MutationEvent("Origin", {}, protein.gene, protein)
        ]
        self._origin = origin

    def add(self, evt: MutationEvent):
        self._generations.append(evt)

    def current_gene(self) -> Sequence[int]:
        return self._generations[-1].output

    def current_protein(self) -> Protein:
        return self._generations[-1].protein

    def clone(self) -> Self:
        return Lineage(self.current_protein(), self)


class Mutagenesis:
    __slots__ = ("life",)

    MUTATIONS: List[Type[Mutation]] = [Substitution, Insertion, Deletion, Duplication]

    def __init__(self, life: Life):
        self.life = life

    def random_mutation(self, gene: Sequence[int]) -> MutationEvent:
        mutation_cls = self.life.rng.choice(self.MUTATIONS)
        mutation = mutation_cls(self.life, gene)
        return mutation.random()

    def diverge(self, origin: Lineage) -> Lineage:
        nb_args = origin.current_protein().nb_inputs
        lineage = origin.clone()
        step = 0
        while True:
            step += 1
            try:
                mutation_event = self.random_mutation(lineage.current_gene())
                protein = self.life.dna_to_protein(mutation_event.output)
                if protein.nb_inputs != nb_args:
                    raise ProteinArgsError(nb_args, protein.nb_inputs)
                mutation_event.protein = protein
                lineage.add(mutation_event)
                break
            except DNAError:
                pass
        return lineage
