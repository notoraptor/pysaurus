import math
import operator
import random
from abc import ABC, abstractmethod
from typing import List

from pysaurus.core.classes import StringPrinter


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


class Function(ABC):
    def __init__(self, nb_inputs: int, name=None):
        self.nb_inputs = nb_inputs
        self.name: str = (name or type(self).__name__).lower()

    def __repr__(self):
        output = self.name
        if self.nb_inputs:
            output += (
                f"({', '.join(Utils.get_arg_name(i) for i in range(self.nb_inputs))})"
            )
        return output

    def uid(self):
        return Utils.generate_uid(self.name)

    def __call__(self, *args):
        return self.run(*args)

    @abstractmethod
    def run(self, *args):
        raise NotImplementedError()


class GenericFunction(Function):
    def __init__(self, function: callable, nb_inputs: int, name=None):
        super().__init__(nb_inputs, name or function.__name__)
        self.function = function

    def run(self, *args):
        return self.function(*args)


class Const(Function):
    def __init__(self):
        super().__init__(1)

    def run(self, const):
        return const


class StaticConstant(Function):
    def __init__(self, const, name):
        super().__init__(0, name)
        self.const = const

    def run(self, *args):
        return self.const


class Feed(Function):
    def __init__(self):
        super().__init__(0)

    def run(self, *args):
        raise ValueError("Please, feed me.")


CONST_PI = StaticConstant(math.pi, "pi")
CONST_E = StaticConstant(math.e, "e")
CONST_TAU = StaticConstant(math.tau, "tau")
CONST_INF = StaticConstant(math.inf, "inf")
CONST_NAN = StaticConstant(math.nan, "nan")
CONST_0 = StaticConstant(0, "_0")
CONST_1 = StaticConstant(1, "_1")
CONST_2 = StaticConstant(2, "_2")
CONST_3 = StaticConstant(3, "_3")
CONST_4 = StaticConstant(4, "_4")
CONST_5 = StaticConstant(5, "_5")
CONST_6 = StaticConstant(6, "_6")
CONST_7 = StaticConstant(7, "_7")
CONST_8 = StaticConstant(8, "_8")
CONST_9 = StaticConstant(9, "_9")
CONST_10 = StaticConstant(10, "_10")
CONST_100 = StaticConstant(100, "_100")
CONST_1000 = StaticConstant(1000, "_1000")
CONST_1000000000 = StaticConstant(1_000_000_000, "_1000000000")


def boolean_and(a, b):
    return a and b


def boolean_or(a, b):
    return a or b


def if_else(x, y, z):
    return y if x else z


CODONS = [
    # -- basic operators
    # math binary operators
    GenericFunction(operator.add, 2),
    GenericFunction(operator.sub, 2),
    GenericFunction(operator.mul, 2),
    GenericFunction(operator.truediv, 2, "div"),
    GenericFunction(operator.floordiv, 2, "euc"),
    GenericFunction(operator.mod, 2),
    GenericFunction(operator.pow, 2),
    # boolean binary operators
    GenericFunction(operator.eq, 2),
    GenericFunction(operator.ne, 2),
    GenericFunction(operator.lt, 2),
    GenericFunction(operator.le, 2),
    GenericFunction(operator.gt, 2),
    GenericFunction(operator.ge, 2),
    # boolean unary operator
    GenericFunction(operator.not_, 1),
    # bitwise binary operators
    GenericFunction(operator.and_, 2),
    GenericFunction(operator.or_, 2),
    GenericFunction(operator.xor, 2),
    GenericFunction(operator.lshift, 2, "lsh"),
    GenericFunction(operator.rshift, 2, "rsh"),
    # bitwise unary operator
    GenericFunction(operator.inv, 1),
    # unary operators
    GenericFunction(operator.abs, 1),
    GenericFunction(operator.neg, 1),
    GenericFunction(operator.pos, 1),  # identity
    # -- constants
    CONST_PI,
    CONST_E,
    CONST_TAU,
    CONST_INF,
    CONST_NAN,
    CONST_0,
    CONST_1,
    CONST_2,
    CONST_3,
    CONST_4,
    CONST_5,
    CONST_6,
    CONST_7,
    CONST_8,
    CONST_9,
    CONST_10,
    CONST_100,
    CONST_1000,
    CONST_1000000000,
    # -- complex operators
    GenericFunction(math.isfinite, 1, "isnb"),
    GenericFunction(math.isinf, 1),
    GenericFunction(math.isnan, 1),
    GenericFunction(math.sqrt, 1),
    GenericFunction(math.exp, 1),
    GenericFunction(math.log, 2),
    GenericFunction(math.log2, 1),
    GenericFunction(math.log10, 1),
    GenericFunction(math.sin, 1),
    GenericFunction(math.cos, 1),
    GenericFunction(math.tan, 1),
    GenericFunction(math.asin, 1),
    GenericFunction(math.acos, 1),
    GenericFunction(math.atan, 1),
    GenericFunction(math.degrees, 1, "deg"),
    GenericFunction(math.radians, 1, "rad"),
    # -- Special operators
    Feed(),
    # -- Implementations of boolean operators
    GenericFunction(boolean_and, 2, "and"),
    GenericFunction(boolean_or, 2, "or"),
    GenericFunction(if_else, 3, "if"),
]


class AbstractCodonGenerator(ABC):
    @abstractmethod
    def generate(self) -> int:
        raise NotImplementedError()


class CodonGenerator(AbstractCodonGenerator):
    def __init__(self, codon: Function):
        self.codon = codon
        self.uid = codon.uid()

    def generate(self) -> int:
        return self.uid


class RandomIntegerGenerator(AbstractCodonGenerator):
    def generate(self) -> int:
        """
        Return value in interval [a, b], a and b included.
        Current bounds:
        a: 0
        b: 1 000 000 000
        """
        return random.randint(0, 1_000_000_000)


class Feeder:
    def give(self):
        pass


class RunNode(ABC):
    @abstractmethod
    def execute(self, feeder: Feeder):
        raise NotImplementedError()

    def __repr__(self):
        return self.__str__()

    def debug(self):
        with StringPrinter() as printer:
            self._debug(printer, "")
            return str(printer)

    def _debug(self, printer: StringPrinter, indentation: str):
        printer.write(f"{indentation}{self}")


class FunctionNode(RunNode):
    def __init__(self, function: Function, inputs=()):
        self.function: Function = function
        self.inputs: List[FunctionNode] = list(inputs)

    def __str__(self):
        return str(self.function)

    def _debug(self, printer: StringPrinter, indentation: str):
        super()._debug(printer, indentation)
        for inp in self.inputs:
            inp._debug(printer, indentation + " ")

    def execute(self, feeder: Feeder):
        return self.function.run(*(child.execute(feeder) for child in self.inputs))


class ValueNode(RunNode):
    def __init__(self, constant):
        self.const = constant

    def __str__(self):
        return str(self.const)

    def update(self, constant):
        self.const = constant

    def execute(self, feeder: Feeder):
        return self.const


class FeedNode(RunNode):
    def __str__(self):
        return "?"

    def execute(self, feeder: Feeder):
        return feeder.give()


class ParsingResult:
    def __init__(self, node: RunNode, position: int):
        self.node = node
        self.next_unparsed_position = position


class SequenceGenerator:
    NAME_TO_CODON = {codon.name: codon for codon in CODONS}
    assert len(NAME_TO_CODON) == len(CODONS)
    UID_TO_CODON = {codon.uid(): codon for codon in CODONS}
    assert len(UID_TO_CODON) == len(CODONS)
    GENERATORS: List[AbstractCodonGenerator] = [
        CodonGenerator(codon) for codon in CODONS
    ]  # + [RandomIntegerGenerator()]

    # MIN_LENGTH = 1
    MIN_LENGTH = 2
    # MAX_LENGTH = 1000
    MAX_LENGTH = 10

    def generate(self) -> List[int]:
        return [
            random.choice(self.GENERATORS).generate()
            for _ in range(random.randint(self.MIN_LENGTH, self.MAX_LENGTH))
        ]

    def interpret(self, sequence: List[int]):
        for i, uid in enumerate(sequence):
            if uid in self.UID_TO_CODON:
                print(f"({i + 1}) COD {uid} => {self.UID_TO_CODON[uid]}")
            else:
                print(f"({i + 1}) NUM {uid}")

    def parse_sequence(self, sequence: List[int]) -> RunNode:
        result = self.parse_node(sequence, 0)
        if result.next_unparsed_position != len(sequence):
            raise ValueError(
                f"Sequence parsing requires position "
                f"{result.next_unparsed_position + 1} / {len(sequence)}"
            )
        return result.node

    def parse_node(self, sequence: List[int], position: int) -> ParsingResult:
        uid = sequence[position]
        codon = self.UID_TO_CODON[uid]
        # print(position + 1, codon)
        if isinstance(codon, GenericFunction):
            inputs = []
            pos = position + 1
            for _ in range(codon.nb_inputs):
                child_result = self.parse_node(sequence, pos)
                inputs.append(child_result.node)
                pos = child_result.next_unparsed_position
            node = FunctionNode(codon, inputs)
            ret = ParsingResult(node, pos)
        elif isinstance(codon, StaticConstant):
            node = ValueNode(codon.run())
            ret = ParsingResult(node, position + 1)
        elif isinstance(codon, Feed):
            node = FeedNode()
            ret = ParsingResult(node, position + 1)
        else:
            raise NotImplementedError(f"Unknown codon: {uid} => {codon}")
        return ret


def main_():
    seq_gen = SequenceGenerator()
    seq1 = seq_gen.generate()
    seq_gen.interpret(seq1)
    seq_gen.parse_sequence(seq1)


def main():
    sequence_generator = SequenceGenerator()
    iteration = 0
    while True:
        iteration += 1
        seq = sequence_generator.generate()
        try:
            node = sequence_generator.parse_sequence(seq)
            print("Sequence:")
            sequence_generator.interpret(seq)
            print()
            print("Node:")
            print(node.debug())
            print(f"[step {iteration}] success")
            break
        except Exception as exc:
            print(f"[step {iteration}, seq len {len(seq)}]", type(exc).__name__, exc)
            continue


if __name__ == "__main__":
    main()
