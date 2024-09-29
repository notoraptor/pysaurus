import operator
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Self, Sequence, Tuple, Union

from pysaurus.core import functions


class Incrementer:
    __slots__ = ("_count",)

    def __init__(self):
        self._count = 0

    def next(self) -> int:
        self._count += 1
        return self._count


INCREMENTER = Incrementer()


def _name_of(something):
    if isinstance(something, Variable):
        return repr(something)
    if hasattr(something, "__qualname__"):
        return something.__qualname__
    if hasattr(something, "__name__"):
        return something.__name__
    return repr(something)


def _binary_op_method(function):
    def method(self, other):
        return Function(function, self, other)

    return method


class Variable(ABC):
    __slots__ = ("order",)

    def __init__(self):
        self.order = INCREMENTER.next()

    def __repr__(self):
        return type(self).__name__

    @abstractmethod
    def run(self, space: Dict[str, Any]) -> Any:
        raise NotImplementedError()

    def __getattr__(self, item) -> Self:
        return Function(getattr, self, item)

    def __call__(self, *args, **kwargs) -> Self:
        return Function(self, *args, **kwargs)

    def __add__(self, other) -> Self:
        return Function(operator.add, self, other)

    def __sub__(self, other) -> Self:
        return Function(operator.sub, self, other)

    def __mul__(self, other) -> Self:
        return Function(operator.mul, self, other)

    def __truediv__(self, other) -> Self:
        return Function(operator.truediv, self, other)

    def __floordiv__(self, other) -> Self:
        return Function(operator.floordiv, self, other)

    def __mod__(self, other) -> Self:
        return Function(operator.mod, self, other)

    def __pow__(self, power, modulo=None) -> Self:
        return Function(operator.pow, self, power)

    def __radd__(self, other) -> Self:
        return self.__add__(other)

    def __rsub__(self, other) -> Self:
        return Function(operator.add, -self, other)

    def __rmul__(self, other) -> Self:
        return self.__mul__(other)

    def __rtruediv__(self, other) -> Self:
        return Function(operator.truediv, other, self)

    def __rfloordiv__(self, other) -> Self:
        return Function(operator.floordiv, other, self)

    def __rmod__(self, other) -> Self:
        return Function(operator.mod, other, self)

    def __rpow__(self, other) -> Self:
        return Function(operator.pow, other, self)

    def __eq__(self, other) -> Self:
        return Function(operator.eq, self, other)

    def __ne__(self, other) -> Self:
        return Function(operator.ne, self, other)

    def __lt__(self, other) -> Self:
        return Function(operator.lt, self, other)

    def __gt__(self, other) -> Self:
        return Function(operator.gt, self, other)

    def __le__(self, other) -> Self:
        return Function(operator.le, self, other)

    def __ge__(self, other) -> Self:
        return Function(operator.ge, self, other)

    def __and__(self, other) -> Self:
        return Function(operator.and_, self, other)

    def __rand__(self, other) -> Self:
        return Function(operator.and_, other, self)

    def __or__(self, other) -> Self:
        return Function(operator.or_, self, other)

    def __ror__(self, other) -> Self:
        return Function(operator.or_, other, self)

    def __xor__(self, other) -> Self:
        return Function(operator.xor, self, other)

    def __rxor__(self, other) -> Self:
        return Function(operator.xor, other, self)

    def __lshift__(self, other) -> Self:
        return Function(operator.lshift, self, other)

    def __rlshift__(self, other) -> Self:
        return Function(operator.lshift, other, self)

    def __rshift__(self, other) -> Self:
        return Function(operator.rshift, self, other)

    def __rrshift__(self, other) -> Self:
        return Function(operator.rshift, other, self)

    def __invert__(self) -> Self:
        return Function(operator.inv, self)

    def __neg__(self) -> Self:
        return Function(operator.neg, self)

    def __pos__(self) -> Self:
        return Function(operator.pos, self)

    def __abs__(self) -> Self:
        return Function(abs, self)


class Reference(Variable):
    __slots__ = ("_name",)

    def __init__(self, name: str):
        super().__init__()
        self._name = name

    def __repr__(self):
        return self._name

    @property
    def name(self) -> str:
        return self._name

    def run(self, space: Dict[str, Any]) -> Any:
        return space[self._name]


class Value(Variable):
    __slots__ = ("_value",)

    def __init__(self, value):
        super().__init__()
        self._value = value

    def __repr__(self):
        return _name_of(self._value)

    def run(self, space: Dict[str, Any]) -> Any:
        return self._value


class Expression(Variable):
    __slots__ = ()


class Function(Expression):
    __slots__ = ("_function", "_args", "_kwargs")

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self._function = self._wrap(function)
        self._args = [self._wrap(arg) for arg in args]
        self._kwargs = {
            self._assert_str(key): self._wrap(value) for key, value in kwargs.items()
        }

    def __repr__(self):
        output = (
            f"{_name_of(self._function)}({', '.join(repr(arg) for arg in self._args)}"
        )
        if self._kwargs:
            output += " " + ", ".join(
                f"{key}={value}" for key, value in self._kwargs.items()
            )
        return output + ")"

    @staticmethod
    def _assert_str(value):
        assert isinstance(value, str)
        return value

    @staticmethod
    def _assert_expr(value) -> Expression:
        assert isinstance(value, Expression)
        return value

    @staticmethod
    def _wrap(something) -> Variable:
        return something if isinstance(something, Variable) else Value(something)

    def run(self, space: Dict[str, Any]) -> Any:
        return (self._function.run(space))(
            *(arg.run(space) for arg in self._args),
            **{key: value.run(space) for key, value in self._kwargs.items()},
        )


class ExprSet(Expression):
    def __init__(self, reference: Reference, variable: Variable):
        super().__init__()
        self._ref = reference
        self._var = variable

    def __repr__(self):
        return f"{self._ref.name} = {self._var}"

    def run(self, space: Dict[str, Any]) -> Any:
        space[self._ref.name] = self._var.run(space)


class Lambda:
    def __init__(
        self,
        arguments: Union[Reference, Tuple[Reference, ...]],
        body: Sequence[Expression],
    ):
        if isinstance(arguments, Reference):
            arguments = (arguments,)
        else:
            assert isinstance(arguments, tuple)
            for argument in arguments:
                assert isinstance(argument, Reference)
        assert len(set(arg.name for arg in arguments)) == len(arguments)

        body = [Function._wrap(expr) for expr in body]

        self._arguments: Tuple[Reference, ...] = arguments
        self._body: List[Expression] = body

    def __call__(self, *args):
        if len(args) != len(self._arguments):
            raise RuntimeError(
                f"Expected {len(self._arguments)} arguments, got {len(args)}"
            )
        space = {ref.name: args[i] for i, ref in enumerate(self._arguments)}
        ret = None
        for expr in self._body:
            ret = expr.run(space)
        return ret


class ReferenceFactory:
    def __getattr__(self, item) -> Reference:
        return Reference(item)


class ExpressionFactory:
    def set(self, reference: Reference, variable: Variable) -> Expression:
        return ExprSet(reference, variable)

    def and_(self, a: Variable, b: Variable) -> Function:
        return Function(functions.boolean_and, a, b)

    def or_(self, a: Variable, b: Variable) -> Function:
        return Function(functions.boolean_or, a, b)

    def not_(self, variable: Variable) -> Function:
        return Function(operator.not_, variable)

    def return_(self, variable: Variable) -> Expression:
        return Function(functions.identity, variable)


V = ReferenceFactory()
E = ExpressionFactory()
