from abc import abstractmethod, ABC
import operator
import math


UID_MAP = {
    **{c: i + 1 for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")},
    "_": 89,
    **{i: 90 + i for i in range(10)},
    **{str(i): 90 + i for i in range(10)},
}
assert len(UID_MAP) == 47

ARG_NAMES = list("xyzabcdefghijklmnopqrstuvw")
assert len(ARG_NAMES) == 26


def get_arg_name(i):
    return ARG_NAMES[i] if i < len(ARG_NAMES) else f"x{i + 1}"


class Function(ABC):

    def __init__(self, nb_inputs: int, name=None):
        self.nb_inputs = nb_inputs
        self.name = (name or type(self).__name__).lower()

    def __str__(self):
        output = self.name
        if self.nb_inputs:
            output += f"({', '.join(get_arg_name(i) for i in range(self.nb_inputs))})"
        return output

    __repr__ = __str__

    def uid(self):
        digits = list(self.name) + [self.nb_inputs]
        return sum(UID_MAP[d] * 100 ** i for i, d in enumerate(reversed(digits)))

    def __call__(self, *args):
        assert len(args) == self.nb_inputs
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


CONST_PI = StaticConstant(math.pi, "pi")
CONST_E = StaticConstant(math.e, "e")
CONST_TAU = StaticConstant(math.tau, "tau")
CONST_INF = StaticConstant(math.inf, "inf")
CONST_NAN = StaticConstant(math.nan, "nan")


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
    Const(),
]


def main():
    print("Codons:", len(CODONS))
    names = set()
    uids = set()
    for i, codon in enumerate(CODONS):
        cuid = codon.uid()
        print(f"({i + 1}) {codon} ; {cuid}")
        assert codon.name not in names, (codon, cuid)
        assert cuid not in uids, (codon, cuid)
        names.add(codon.name)
        uids.add(cuid)


if __name__ == '__main__':
    main()
