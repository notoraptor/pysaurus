from dataclasses import dataclass
from typing import Sequence

from wip.adnoide.adnoide import (
    CODON_TO_FUNCTION,
    CODONS,
    AbstractFunctionNode,
    Constant,
    ConstantNode,
    Feed,
    FeedNode,
    Function,
    FunctionNode,
    Life,
    Protein,
)
from wip.adnoide.dna_errors import (
    DNATooLongForTranslationError,
    DNATooShortForTranslationError,
)


class UtilsOld:
    ARG_NAMES = list("xyzabcdefghijklmnopqrstuvw")
    assert len(ARG_NAMES) == 26

    UID_ENCODER = {
        **{c: ord(c) - ord("a") + 1 for c in ARG_NAMES},
        "_": 89,
        **{str(i): 90 + i for i in range(10)},
    }
    assert len(UID_ENCODER) == 37

    @classmethod
    def unum(cls, name: str) -> int:
        # Generate Unique NUMber (unique ID) from a given name.
        return sum(cls.UID_ENCODER[d] * 100**i for i, d in enumerate(reversed(name)))

    @classmethod
    def argname(cls, i: int) -> str:
        return cls.ARG_NAMES[i] if i < len(cls.ARG_NAMES) else f"x{i + 1}"


class ProteinGenerator:
    def __init__(self, gen: Life):
        seq = []
        self.gen = gen
        self.nb_feeds = 0
        node = self._gof(seq)
        self.protein = Protein(node=node, nb_inputs=self.nb_feeds, gene=seq)

    def _gof(self, seq: list[int]) -> AbstractFunctionNode:
        """[g]enerate [o]n [f]ly"""
        if len(seq) > self.gen.max_length:
            raise DNATooLongForTranslationError(f"{len(seq)} / {self.gen.max_length}")

        codon = self.gen.rng.choice(CODONS)
        func = CODON_TO_FUNCTION[codon]
        seq.append(codon)
        if isinstance(func, Function):
            inputs = [self._gof(seq) for _ in range(len(func.input_types))]
            node = FunctionNode(func, inputs)
        elif isinstance(func, Constant):
            node = ConstantNode(func)
        elif isinstance(func, Feed):
            self.nb_feeds += 1
            node = FeedNode()
        else:
            raise NotImplementedError(f"Unknown function: {codon} => {func}")
        return node


@dataclass(slots=True)
class ParsingResult:
    node: AbstractFunctionNode
    next_unparsed_position: int


class Ribosome0:
    __slots__ = ("_nb_feeds", "protein")

    def __init__(self, gene: Sequence[int]):
        self._nb_feeds = 0
        result = self._parse_codons(gene, 0)
        if result.next_unparsed_position != len(gene):
            raise DNATooLongForTranslationError(
                result.next_unparsed_position + 1, len(gene)
            )
        self.protein = Protein(
            node=result.node, nb_inputs=int(self._nb_feeds), gene=gene
        )

    def _parse_codons(self, sequence: Sequence[int], position: int) -> ParsingResult:
        if position >= len(sequence):
            raise DNATooShortForTranslationError(position + 1, len(sequence))
        codon = sequence[position]
        function = CODON_TO_FUNCTION[codon]
        if isinstance(function, Function):
            inputs = []
            pos = position + 1
            for _ in range(len(function.input_types)):
                child_result = self._parse_codons(sequence, pos)
                inputs.append(child_result.node)
                pos = child_result.next_unparsed_position
            node = FunctionNode(function, inputs)
            ret = ParsingResult(node, pos)
        elif isinstance(function, Constant):
            node = ConstantNode(function)
            ret = ParsingResult(node, position + 1)
        elif isinstance(function, Feed):
            self._nb_feeds += 1
            node = FeedNode()
            ret = ParsingResult(node, position + 1)
        else:
            raise NotImplementedError(f"Unknown function: {codon} => {function}")
        return ret
