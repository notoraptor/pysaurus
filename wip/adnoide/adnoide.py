import inspect
import math
import operator
import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Self, Sequence, Tuple, Union

from pysaurus.core.classes import StringPrinter
from pysaurus.core.functions import boolean_and, boolean_or, if_else, map_attribute
from wip.adnoide.dna_errors import (
    DNATooLongForTranslationError, DNATooShortForTranslationError,
    ProteinError,
    ProteinTypeError,
)


class Utils:
    @classmethod
    def unum(cls, name: str) -> int:
        # Generate Unique NUMber (unique ID) from a given name.
        return sum(cls._char_to_num(d) * 100**i for i, d in enumerate(reversed(name)))

    @classmethod
    def _char_to_num(cls, c: str):
        if "a" <= c <= "z":
            return ord(c) - ord("a") + 1  # a -> 1, z -> 26
        elif c == "_":
            return 89
        elif "0" <= c <= "9":
            return 90 + ord(c) - ord("0")  # 0 -> 90, 9 -> 99
        raise ValueError(f"Unhandled character: {c}")

    @classmethod
    def argname(cls, i: int) -> str:
        """Get arg name in "xyzabc...uvw" or f"x{i + 1}" for greater arg positions."""
        return chr(ord("a") + (26 + i - 3) % 26) if i < 26 else f"x{i + 1}"


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
            raise ProteinTypeError(f"Expected type {self}, got type {food_type}")


Anything = FoodType([object], strict=False, name="Anything")
Numeric = FoodType((bool, int, float), name="Numeric")
Int = FoodType([int], name="Int")
Float = FoodType([float], name="Float")
Bool = FoodType([bool], name="Bool")
TYPE_TO_FOOD_TYPE = {bool: Bool, int: Int, float: Float, object: Anything}


class AbstractFunction(ABC):
    __slots__ = ("name", "unique_id", "input_types", "output_type")

    def __init__(
        self,
        name=None,
        input_types: Union[int, Sequence[FoodType]] = (),
        output_type: FoodType = Numeric,
    ):
        if isinstance(input_types, int):
            input_types = [Numeric] * input_types

        self.name: str = (name or type(self).__name__).lower()
        self.unique_id: int = Utils.unum(self.name)
        self.input_types: Tuple[FoodType, ...] = tuple(input_types)
        self.output_type: FoodType = output_type or Numeric

    def __hash__(self):
        return hash((self.unique_id, self.input_types, self.output_type))

    def __eq__(self, other: "AbstractFunction"):
        return (
            self.unique_id == other.unique_id
            and self.input_types == other.input_types
            and self.output_type == other.output_type
        )

    def __repr__(self):
        output = self.name
        if self.input_types:
            output += (
                f"({', '.join(Utils.argname(i) for i in range(len(self.input_types)))})"
            )
        return output


class Function(AbstractFunction):
    __slots__ = ("function",)

    def __init__(
        self,
        function: callable,
        input_types: Union[int, Sequence[FoodType]] = (),
        output_type=None,
        name=None,
    ):
        super().__init__(name or function.__name__, input_types, output_type)
        self.function = function


class Constant(AbstractFunction):
    __slots__ = ("const",)

    def __init__(self, const, name):
        super().__init__(name, 0, TYPE_TO_FOOD_TYPE[type(const)])
        self.const = const


class Feed(AbstractFunction):
    __slots__ = ()

    def __init__(self):
        super().__init__(input_types=0, output_type=Anything)

    def __repr__(self):
        return "?"


FEED = Feed()


class AbstractCursor[T](ABC):
    __slots__ = ("_sequence",)

    def __init__(self, sequence: Sequence[T]):
        self._sequence = sequence

    def sequence(self) -> Sequence[T]:
        return self._sequence

    @abstractmethod
    def next(self) -> T:
        raise NotImplementedError()

    @abstractmethod
    def remains(self) -> bool:
        raise NotImplementedError()


class AbstractLimitedCursor[T](AbstractCursor[T]):
    __slots__ = ("_cursor",)

    def __init__(self, sequence: Sequence[T]):
        super().__init__(sequence)
        self._cursor = 0

    def next(self) -> T:
        element = self._sequence[self._cursor]
        self._cursor += 1
        return element

    def remains(self) -> bool:
        return len(self._sequence) - self._cursor > 0


class Feeder(AbstractLimitedCursor[Any]):
    __slots__ = ()


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
        tasks = [(self, 0)]
        with StringPrinter() as printer:
            while tasks:
                node, indt = tasks.pop()
                tasks.extend((child, indt + 1) for child in reversed(node.input_nodes))
                printer.write(f"{'  ' * indt}{node}")
            return str(printer)

    def expect_type(self):
        for i, input_type in enumerate(self.function.input_types):
            node = self.input_nodes[i]
            node.expect_type()
            if node.function != FEED:
                input_type.expect_type(node.function.output_type)

    @abstractmethod
    def execute(self, feeder: Feeder):
        raise NotImplementedError()


class FunctionNode(AbstractFunctionNode):
    __slots__ = ()
    function: Function

    def execute(self, feeder: Feeder):
        args = [child.execute(feeder) for child in self.input_nodes]
        try:
            return self.function.function(*args)
        except MemoryError as exc:
            raise MemoryError(self.function.function, args) from exc


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
        return feeder.next()


class Protein:
    __slots__ = ("node", "nb_inputs", "gene")

    def __init__(self, node: AbstractFunctionNode, nb_inputs: int, gene: Sequence[int]):
        node.expect_type()
        self.node = node
        self.nb_inputs = nb_inputs
        self.gene: Tuple[int, ...] = tuple(gene)

    @classmethod
    def _count_feeds(cls, node: AbstractFunctionNode):
        return (
            1
            if isinstance(node, FeedNode)
            else sum((cls._count_feeds(c) for c in node.input_nodes))
        )

    def __hash__(self):
        return hash((self.node, self.nb_inputs, self.gene))

    def __eq__(self, other: "Protein"):
        return (
            self.node == other.node
            and self.nb_inputs == other.nb_inputs
            and self.gene == other.gene
        )

    def __repr__(self):
        return self.node.describe()

    def __call__(self, *args):
        if len(args) != self.nb_inputs:
            raise ProteinError(f"Expected {self.nb_inputs} args, given {len(args)}")
        return self.node.execute(Feeder(args))


FUNCTIONS: List[AbstractFunction] = [
    # -- basic operators
    # math binary operators
    Function(operator.add, 2),
    Function(operator.sub, 2),
    Function(operator.mul, 2),
    Function(operator.truediv, 2, name="div"),
    Function(operator.floordiv, 2, name="euc"),
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
    Function(operator.not_, [Anything], Bool),
    # bitwise binary operators
    Function(operator.and_, [Int, Int], Int),
    Function(operator.or_, [Int, Int], Int),
    Function(operator.xor, [Int, Int], Int),
    Function(operator.lshift, [Int, Int], Int, "lsh"),
    Function(operator.rshift, [Int, Int], Int, "rsh"),
    # bitwise unary operator
    Function(operator.inv, [Int], Int),
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
    Function(math.isfinite, 1, Bool, "noinf"),
    Function(math.isinf, 1, Bool),
    Function(math.isnan, 1, Bool),
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
    Function(math.degrees, 1, name="deg"),
    Function(math.radians, 1, name="rad"),
    # -- Special operators
    FEED,
    # -- Implementations of boolean operators
    Function(boolean_and, [Anything, Anything], Anything, "and"),
    Function(boolean_or, [Anything, Anything], Anything, "or"),
    Function(if_else, [Anything, Anything, Anything], Anything, "if"),
]
CODON_TO_FUNCTION: Dict[int, AbstractFunction] = map_attribute(FUNCTIONS, "unique_id")
CODONS: List[int] = sorted(CODON_TO_FUNCTION)


class Life:
    __slots__ = ("rng", "min_length", "max_length")

    def __init__(self, seed: int = None, min_length=2, max_length=20):
        assert 0 <= min_length <= max_length
        self.rng = random.Random(seed)
        self.min_length = min_length
        self.max_length = max_length

    def randint(self, a, b) -> int:
        return self.rng.randint(a, b)

    def random_codon(self) -> int:
        return self.rng.choice(CODONS)

    def random_dna(self, min_length=None, max_length=None) -> List[int]:
        if min_length is None:
            min_length = self.min_length
        if max_length is None:
            max_length = self.max_length
        return [
            self.rng.choice(CODONS)
            for _ in range(self.rng.randint(min_length, max_length))
        ]

    def random_protein(self) -> Protein:
        return Ribosome(RandomGene(self)).protein

    @classmethod
    def dna_to_protein(cls, sequence: Sequence[int]) -> Protein:
        return Ribosome(Gene(sequence)).protein

    @classmethod
    def aminoacid(cls, codon: int) -> AbstractFunction:
        return CODON_TO_FUNCTION[codon]


class AbstractGene(AbstractCursor[int]):
    __slots__ = ()


class Gene(AbstractGene, AbstractLimitedCursor[int]):
    __slots__ = ()


class RandomGene(AbstractGene):
    __slots__ = ("_sequence", "_gen")
    _sequence: List[int]

    def __init__(self, generator: Life):
        super().__init__([])
        self._gen = generator

    def next(self) -> int:
        codon = self._gen.random_codon()
        self._sequence.append(codon)
        return codon

    def remains(self) -> bool:
        return len(self._sequence) < self._gen.max_length


class Ribosome:
    __slots__ = ("_nb_feeds", "protein")
    MAX_GENE_LENGTH = 500

    def __init__(self, gene: AbstractGene):
        self._nb_feeds = 0
        self.protein = Protein(self._parse_gene(gene), self._nb_feeds, gene.sequence())

    def _parse_gene(self, gene: AbstractGene) -> AbstractFunctionNode:
        if len(gene.sequence()) >= self.MAX_GENE_LENGTH:
            raise DNATooLongForTranslationError(self.MAX_GENE_LENGTH)
        if not gene.remains():
            raise DNATooShortForTranslationError(gene)

        codon = gene.next()
        function = Life.aminoacid(codon)
        if isinstance(function, Function):
            inputs = [self._parse_gene(gene) for _ in range(len(function.input_types))]
            node = FunctionNode(function, inputs)
        elif isinstance(function, Constant):
            node = ConstantNode(function)
        elif isinstance(function, Feed):
            self._nb_feeds += 1
            node = FeedNode()
        else:
            raise NotImplementedError(f"Unknown function: {codon} => {function}")
        return node
