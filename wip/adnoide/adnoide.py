import inspect
import math
import operator
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Self, Sequence, Tuple

from pysaurus.core.classes import StringPrinter
from pysaurus.core.functions import boolean_and, boolean_or, if_else, map_attribute
from wip.adnoide.dna_errors import (
    DNATooLongForTranslationError,
    DNATooShortForTranslationError,
    ProteinError,
)


class Utils:
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


class FoodType:
    def __init__(self, basic_types: Sequence, strict=True, name=None):
        assert basic_types
        assert all(inspect.isclass(typ) for typ in basic_types)
        self.basic_types = tuple(basic_types)
        self.strict = bool(strict)
        self.name = name

    def __hash__(self):
        return hash((self.basic_types, self.strict))

    def __eq__(self, other: "FoodType"):
        return self.basic_types == other.basic_types and self.strict == other.strict

    def __repr__(self):
        name = self.name or f"Type{self.basic_types}"
        return f"{name}" + ("" if self.strict else "...")

    def is_valid_value(self, value) -> bool:
        if self.strict:
            return type(value) in self.basic_types
        else:
            return isinstance(value, self.basic_types)

    def is_valid_type(self, food_type: Self) -> bool:
        if self.strict:
            return all(typ in self.basic_types for typ in food_type.basic_types)
        else:
            return any(
                issubclass(typ, self.basic_types) for typ in food_type.basic_types
            )

    def expect_value(self, value):
        if not self.is_valid_value(value):
            raise TypeError(f"Expected {self}, got {type(value)}: {value}")

    def expect_type(self, food_type: Self) -> None:
        if not self.is_valid_type(food_type):
            raise TypeError(f"Expected type {self}, got type {food_type}")


Anything = FoodType([object], strict=False, name="Anything")
Numeric = FoodType((bool, int, float), name="Numeric")
Int = FoodType([int], name="Int")
Float = FoodType([float], name="Float")
Bool = FoodType([bool], name="Bool")
TYPE_TO_FOOD_TYPE = {bool: Bool, int: Int, float: Float, object: Anything}


class AbstractFunction(ABC):
    __slots__ = ("name", "__uid", "_input_types", "_output_type")

    def __init__(
        self,
        nb_inputs: int,
        name=None,
        input_types: Sequence[FoodType] = (),
        output_type: FoodType = Numeric,
    ):
        if not input_types:
            input_types = [Numeric] * nb_inputs
        assert len(input_types) == nb_inputs
        output_type = output_type or Numeric

        self.name: str = (name or type(self).__name__).lower()
        self.__uid: int = Utils.unum(self.name)
        self._input_types: Tuple[FoodType, ...] = tuple(input_types)
        self._output_type: FoodType = output_type

    @property
    def nb_inputs(self) -> int:
        return len(self._input_types)

    @property
    def unique_id(self) -> int:
        return self.__uid

    @property
    def input_types(self) -> Tuple[FoodType, ...]:
        return self._input_types

    @property
    def output_type(self) -> FoodType:
        return self._output_type

    def __hash__(self):
        return hash((self.__uid, self._input_types, self._output_type))

    def __eq__(self, other: "AbstractFunction"):
        return (
            self.__uid == other.unique_id
            and self._input_types == other.input_types
            and self._output_type == other.output_type
        )

    def __repr__(self):
        output = self.name
        if self.nb_inputs:
            output += f"({', '.join(Utils.argname(i) for i in range(self.nb_inputs))})"
        return output


class Function(AbstractFunction):
    __slots__ = ("function",)

    def __init__(
        self,
        function: callable,
        nb_inputs: int,
        name=None,
        input_types=(),
        output_type=None,
    ):
        super().__init__(
            nb_inputs,
            name or function.__name__,
            input_types=input_types,
            output_type=output_type,
        )
        self.function = function


class Constant(AbstractFunction):
    __slots__ = ("_const",)

    def __init__(self, const, name):
        super().__init__(0, name, output_type=TYPE_TO_FOOD_TYPE[type(const)])
        self._const = const

    const = property(lambda self: self._const)


class Feed(AbstractFunction):
    __slots__ = ()

    def __init__(self):
        super().__init__(0, output_type=Anything)

    def __repr__(self):
        return "?"


FEED = Feed()


class Feeder:
    __slots__ = ("_food", "_cursor")

    def __init__(self, food: Sequence):
        self._food = food
        self._cursor = 0

    def give(self):
        meal = self._food[self._cursor]
        self._cursor += 1
        return meal


class AbstractFunctionNode(ABC):
    __slots__ = ("function", "input_nodes")

    def __init__(self, function: AbstractFunction, inputs=()):
        self.function = function
        self.input_nodes: Tuple[AbstractFunctionNode, ...] = tuple(inputs)

    def __hash__(self):
        return hash((self.function, self.input_nodes))

    def __eq__(self, other: "AbstractFunctionNode"):
        return self.function == other.function and self.input_nodes == other.input_nodes

    def __repr__(self):
        return f"{self.function} [{self.function.unique_id}]"

    def describe(self):
        with StringPrinter() as printer:
            self._describe_in(printer)
            return str(printer)

    def _describe_in(self, printer: StringPrinter, indentation=""):
        printer.write(f"{indentation}{self}")
        for child in self.input_nodes:
            child._describe_in(printer, indentation + "  ")

    def expect_type(self):
        for i, expected_type in enumerate(self.function.input_types):
            node = self.input_nodes[i]
            node.expect_type()
            if node.function != FEED:
                expected_type.expect_type(node.function.output_type)

    @abstractmethod
    def execute(self, feeder: Feeder):
        raise NotImplementedError()


class FunctionNode(AbstractFunctionNode):
    __slots__ = ()
    function: Function

    def __init__(self, function: Function, inputs=()):
        super().__init__(function, inputs)

    def execute(self, feeder: Feeder):
        return self.function.function(
            *(child.execute(feeder) for child in self.input_nodes)
        )


class ConstantNode(AbstractFunctionNode):
    __slots__ = ()
    function: Constant

    def __init__(self, constant: Constant):
        super().__init__(constant)

    def execute(self, feeder: Feeder):
        return self.function.const


class FeedNode(AbstractFunctionNode):
    __slots__ = ()
    function: Feed

    def __init__(self):
        super().__init__(FEED)

    def execute(self, feeder: Feeder):
        return feeder.give()


class Protein:
    __slots__ = ("node", "nb_inputs", "sequence")

    def __init__(
        self, node: AbstractFunctionNode, nb_inputs: int, sequence: Sequence[int]
    ):
        node.expect_type()
        self.node = node
        self.nb_inputs = nb_inputs
        self.sequence: Tuple[int, ...] = tuple(sequence)

    def __hash__(self):
        return hash((self.node, self.nb_inputs, self.sequence))

    def __eq__(self, other: "Protein"):
        return (
            self.node == other.node
            and self.nb_inputs == other.nb_inputs
            and self.sequence == other.sequence
        )

    def _count_feeds(self, node: AbstractFunctionNode):
        return (
            1
            if isinstance(node, FeedNode)
            else sum((self._count_feeds(c) for c in node.input_nodes))
        )

    def __repr__(self):
        return self.node.describe()

    def __call__(self, *args):
        if len(args) != self.nb_inputs:
            raise ProteinError(f"Expected {self.nb_inputs} args, given {len(args)}")
        return self.node.execute(Feeder(args))


@dataclass(slots=True)
class ParsingResult:
    node: AbstractFunctionNode
    next_unparsed_position: int


@dataclass(slots=True)
class Integer:
    v: int = 0

    def __int__(self):
        return self.v


FUNCTIONS: List[AbstractFunction] = [
    # -- basic operators
    # math binary operators
    Function(operator.add, 2),
    Function(operator.sub, 2),
    Function(operator.mul, 2),
    Function(operator.truediv, 2, "div"),
    Function(operator.floordiv, 2, "euc"),
    Function(operator.mod, 2),
    Function(math.pow, 2),
    # boolean binary operators
    Function(operator.eq, 2),
    Function(operator.ne, 2),
    Function(operator.lt, 2),
    Function(operator.le, 2),
    Function(operator.gt, 2),
    Function(operator.ge, 2),
    # boolean unary operator
    Function(operator.not_, 1, input_types=[Anything], output_type=Bool),
    # bitwise binary operators
    Function(operator.and_, 2, input_types=[Int, Int], output_type=Int),
    Function(operator.or_, 2, input_types=[Int, Int], output_type=Int),
    Function(operator.xor, 2, input_types=[Int, Int], output_type=Int),
    Function(operator.lshift, 2, "lsh", input_types=[Int, Int], output_type=Int),
    Function(operator.rshift, 2, "rsh", input_types=[Int, Int], output_type=Int),
    # bitwise unary operator
    Function(operator.inv, 1, input_types=[Int], output_type=Int),
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
    Function(math.isfinite, 1, "noinf", output_type=Bool),
    Function(math.isinf, 1, output_type=Bool),
    Function(math.isnan, 1, output_type=Bool),
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
    FEED,
    # -- Implementations of boolean operators
    Function(boolean_and, 2, "and", [Anything, Anything], Anything),
    Function(boolean_or, 2, "or", [Anything, Anything], Anything),
    Function(if_else, 3, "if", [Anything, Anything, Anything], Anything),
]


class SequenceGenerator:
    CODON_TO_FUNCTION = map_attribute(FUNCTIONS, "unique_id")
    CODONS: List[int] = sorted(CODON_TO_FUNCTION)

    __slots__ = ("rng", "min_length", "max_length")

    def __init__(self, seed: int = None, min_length=2, max_length=20):
        self.rng = random.Random(seed)
        self.min_length = min_length
        self.max_length = max_length

    def generate_dna(self) -> List[int]:
        return [
            self.rng.choice(self.CODONS)
            for _ in range(self.rng.randint(self.min_length, self.max_length))
        ]

    def translate_dna(self, sequence: Sequence[int]) -> Protein:
        nb_feeds = Integer()
        result = self._parse_codon(sequence, 0, nb_feeds)
        if result.next_unparsed_position != len(sequence):
            raise DNATooLongForTranslationError(
                result.next_unparsed_position + 1, len(sequence)
            )
        return Protein(node=result.node, nb_inputs=int(nb_feeds), sequence=sequence)

    def _parse_codon(
        self, sequence: Sequence[int], position: int, nb_feeds: Integer
    ) -> ParsingResult:
        if position >= len(sequence):
            raise DNATooShortForTranslationError(position + 1, len(sequence))
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

    def gof(self) -> Protein:
        """[g]enerate [o]n [f]ly"""
        seq = []
        nb_feeds = Integer()
        node = self._gof(seq, nb_feeds)
        return Protein(node=node, nb_inputs=int(nb_feeds), sequence=seq)

    def _gof(self, seq: List[int], nb_feeds: Integer) -> AbstractFunctionNode:
        if len(seq) > self.max_length:
            raise DNATooLongForTranslationError(f"{len(seq)} / {self.max_length}")

        codon = self.rng.choice(self.CODONS)
        function = self.CODON_TO_FUNCTION[codon]
        seq.append(codon)
        if isinstance(function, Function):
            inputs = []
            for _ in range(function.nb_inputs):
                child_node = self._gof(seq, nb_feeds)
                inputs.append(child_node)
            node = FunctionNode(function, inputs)
        elif isinstance(function, Constant):
            node = ConstantNode(function)
        elif isinstance(function, Feed):
            nb_feeds.v += 1
            node = FeedNode()
        else:
            raise NotImplementedError(f"Unknown function: {codon} => {function}")
        return node
