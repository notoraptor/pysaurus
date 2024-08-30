import math
import operator
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Sequence

from pysaurus.core.classes import StringPrinter
from pysaurus.core.functions import are_hashable_by


class Utils:
    ARG_NAMES = list("xyzabcdefghijklmnopqrstuvw")
    assert len(ARG_NAMES) == 26

    @classmethod
    def get_arg_name(cls, i: int) -> str:
        return cls.ARG_NAMES[i] if i < len(cls.ARG_NAMES) else f"x{i + 1}"

    UID_ENCODER = {
        **{c: i + 1 for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")},
        "_": 89,
        **{i: 90 + i for i in range(10)},
        **{str(i): 90 + i for i in range(10)},
    }
    assert len(UID_ENCODER) == 47

    @classmethod
    def generate_uid(cls, name: str) -> int:
        return sum(cls.UID_ENCODER[d] * 100**i for i, d in enumerate(reversed(name)))


@dataclass(slots=True)
class Integer:
    v: int = 0

    def __int__(self):
        return self.v


class AbstractFunction(ABC):
    __slots__ = ("nb_inputs", "name", "__uid")

    def __init__(self, nb_inputs: int, name=None):
        self.nb_inputs = nb_inputs
        self.name: str = (name or type(self).__name__).lower()
        self.__uid = Utils.generate_uid(self.name)

    @property
    def unique_id(self) -> int:
        return self.__uid

    def __repr__(self):
        output = self.name
        if self.nb_inputs:
            output += (
                f"({', '.join(Utils.get_arg_name(i) for i in range(self.nb_inputs))})"
            )
        return output

    def __call__(self, *args):
        return self.run(*args)

    @abstractmethod
    def run(self, *args):
        raise NotImplementedError()


class Function(AbstractFunction):
    __slots__ = ("function",)

    def __init__(self, function: callable, nb_inputs: int, name=None):
        super().__init__(nb_inputs, name or function.__name__)
        self.function = function

    def run(self, *args):
        return self.function(*args)


class Constant(AbstractFunction):
    __slots__ = ("const",)

    def __init__(self, const, name):
        super().__init__(0, name)
        self.const = const

    def run(self, *args):
        return self.const


class Feed(AbstractFunction):
    __slots__ = ()

    def __init__(self):
        super().__init__(0)

    def __repr__(self):
        return "?"

    def run(self, *args):
        raise ValueError("Please, feed me.")


def boolean_and(a, b):
    return a and b


def boolean_or(a, b):
    return a or b


def if_else(x, y, z):
    return y if x else z


FUNC_FEED = Feed()
FUNCTIONS: List[AbstractFunction] = [
    # -- basic operators
    # math binary operators
    Function(operator.add, 2),
    Function(operator.sub, 2),
    Function(operator.mul, 2),
    Function(operator.truediv, 2, "div"),
    Function(operator.floordiv, 2, "euc"),
    Function(operator.mod, 2),
    Function(operator.pow, 2),
    # boolean binary operators
    Function(operator.eq, 2),
    Function(operator.ne, 2),
    Function(operator.lt, 2),
    Function(operator.le, 2),
    Function(operator.gt, 2),
    Function(operator.ge, 2),
    # boolean unary operator
    Function(operator.not_, 1),
    # bitwise binary operators
    Function(operator.and_, 2),
    Function(operator.or_, 2),
    Function(operator.xor, 2),
    Function(operator.lshift, 2, "lsh"),
    Function(operator.rshift, 2, "rsh"),
    # bitwise unary operator
    Function(operator.inv, 1),
    # unary operators
    Function(operator.abs, 1),
    Function(operator.neg, 1),
    Function(operator.pos, 1),  # identity
    # -- constants
    Constant(math.pi, "pi"),
    Constant(math.e, "e"),
    Constant(math.tau, "tau"),
    Constant(math.inf, "inf"),
    Constant(math.nan, "nan"),
    Constant(0, "_0"),
    Constant(1, "_1"),
    Constant(2, "_2"),
    Constant(3, "_3"),
    Constant(4, "_4"),
    Constant(5, "_5"),
    Constant(6, "_6"),
    Constant(7, "_7"),
    Constant(8, "_8"),
    Constant(9, "_9"),
    Constant(10, "_10"),
    Constant(100, "_100"),
    Constant(1000, "_1000"),
    Constant(1_000_000_000, "_1000000000"),
    # -- complex operators
    Function(math.isfinite, 1, "noinf"),
    Function(math.isinf, 1),
    Function(math.isnan, 1),
    Function(math.sqrt, 1),
    Function(math.exp, 1),
    Function(math.log, 2),
    Function(math.log2, 1),
    Function(math.log10, 1),
    Function(math.sin, 1),
    Function(math.cos, 1),
    Function(math.tan, 1),
    Function(math.asin, 1),
    Function(math.acos, 1),
    Function(math.atan, 1),
    Function(math.degrees, 1, "deg"),
    Function(math.radians, 1, "rad"),
    # -- Special operators
    FUNC_FEED,
    # -- Implementations of boolean operators
    Function(boolean_and, 2, "and"),
    Function(boolean_or, 2, "or"),
    Function(if_else, 3, "if"),
]
assert are_hashable_by(FUNCTIONS, "name")
assert are_hashable_by(FUNCTIONS, "unique_id")


class Feeder:
    __slots__ = ("_food", "_cursor")

    def __init__(self, food: Sequence):
        self._food = food
        self._cursor = 0

    def give(self):
        meal = self._food[self._cursor]
        self._cursor += 1
        return meal


class FunctionNode:
    __slots__ = ("function", "inputs")

    def __init__(self, function: AbstractFunction, inputs=()):
        self.function = function
        self.inputs: List[FunctionNode] = list(inputs)

    def __repr__(self):
        return f"{self.function} [{self.function.unique_id}]"

    def describe(self):
        with StringPrinter() as printer:
            self._describe_in(printer)
            return str(printer)

    def _describe_in(self, printer: StringPrinter, indentation=""):
        printer.write(f"{indentation}{self}")
        for child in self.inputs:
            child._describe_in(printer, indentation + "  ")

    def execute(self, feeder: Feeder):
        return self.function.run(*(child.execute(feeder) for child in self.inputs))


class ConstantNode(FunctionNode):
    __slots__ = ()
    function: Constant

    def __init__(self, constant: Constant):
        super().__init__(constant)


class FeedNode(FunctionNode):
    __slots__ = ()
    function: Feed

    def __init__(self):
        super().__init__(FUNC_FEED)

    def execute(self, feeder: Feeder):
        return feeder.give()


class DNAError(Exception):
    pass


class DNATranslationError(DNAError):
    pass


class ProteinError(DNAError):
    pass


class ConstantProteinError(ProteinError):
    pass


class Protein:
    __slots__ = ("node", "nb_inputs")

    def __init__(self, node: FunctionNode, nb_inputs: int):
        self.node = node
        self.nb_inputs = nb_inputs

    def _count_feeds(self, node: FunctionNode):
        return (
            1
            if isinstance(node, FeedNode)
            else sum((self._count_feeds(c) for c in node.inputs))
        )

    def __repr__(self):
        return self.node.describe()

    def __call__(self, *args):
        if len(args) != self.nb_inputs:
            raise ProteinError(f"Expected {self.nb_inputs} args, given {len(args)}")
        return self.node.execute(Feeder(args))


@dataclass(slots=True)
class ParsingResult:
    node: FunctionNode
    next_unparsed_position: int


class SequenceGenerator:
    NAME_TO_FUNCTION = {function.name: function for function in FUNCTIONS}
    CODON_TO_FUNCTION = {function.unique_id: function for function in FUNCTIONS}
    CODONS: List[int] = sorted(CODON_TO_FUNCTION)

    # MIN_LENGTH = 1
    MIN_LENGTH = 2
    # MAX_LENGTH = 1000
    MAX_LENGTH = 20

    __slots__ = ()

    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)

    def generate_dna(self) -> List[int]:
        return [
            random.choice(self.CODONS)
            for _ in range(random.randint(self.MIN_LENGTH, self.MAX_LENGTH))
        ]

    def translate_dna(self, sequence: List[int]) -> Protein:
        nb_feeds = Integer()
        result = self._parse_codon(sequence, 0, nb_feeds)
        if result.next_unparsed_position != len(sequence):
            raise DNATranslationError(
                f"Unparsed position "
                f"{result.next_unparsed_position + 1} / {len(sequence)}"
            )
        return Protein(node=result.node, nb_inputs=int(nb_feeds))

    def _parse_codon(
        self, sequence: List[int], position: int, nb_feeds: Integer
    ) -> ParsingResult:
        codon = sequence[position]
        function = self.CODON_TO_FUNCTION[codon]
        if isinstance(function, Function):
            inputs = []
            pos = position + 1
            for _ in range(function.nb_inputs):
                child_result = self._parse_codon(sequence, pos, nb_feeds)
                inputs.append(child_result.node)
                pos = child_result.next_unparsed_position
            node = FunctionNode(function, inputs)
            ret = ParsingResult(node, pos)
        elif isinstance(function, Constant):
            node = ConstantNode(function)
            ret = ParsingResult(node, position + 1)
        elif isinstance(function, Feed):
            nb_feeds.v += 1
            node = FeedNode()
            ret = ParsingResult(node, position + 1)
        else:
            raise NotImplementedError(f"Unknown function: {codon} => {function}")
        return ret


def main():
    seq_gen = SequenceGenerator(12345)
    iteration = 0
    while True:
        iteration += 1
        seq = seq_gen.generate_dna()
        try:
            protein = seq_gen.translate_dna(seq)
            print(f"Protein({protein.nb_inputs} args):")
            print(protein)
            if protein.nb_inputs == 0:
                raise ConstantProteinError(protein())
            print(f"[step {iteration}] success")
            break
        except Exception as exc:
            print(f"[step {iteration}, seq len {len(seq)}]", type(exc).__name__, exc)
            continue


if __name__ == "__main__":
    main()
