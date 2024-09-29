import operator
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Tuple, Union


class Incrementer:
    __slots__ = ("_count",)

    def __init__(self):
        self._count = 0

    def next(self) -> int:
        value = self._count
        self._count += 1
        return value


_INCR = Incrementer()


class Apply(ABC):
    def __init__(self):
        self._id = _INCR.next()

    @property
    def order(self) -> int:
        return self._id

    @abstractmethod
    def run(self, space: Dict[str, Any], prev: Any) -> Any:
        raise NotImplementedError()


class Constant(Apply):
    def __init__(self, value):
        assert not isinstance(value, Apply)
        super().__init__()
        self._v = value

    def __repr__(self):
        return repr(self._v)

    def run(self, space: Dict[str, Any], prev: Any) -> Any:
        return self._v


def _wrap(something) -> Apply:
    return something if isinstance(something, Apply) else Constant(something)


class _ApplyFunction(Apply):
    def __init__(self, function: callable, *inputs: Apply):
        super().__init__()
        self._function = function
        self._inputs = [_wrap(inp) for inp in inputs]

    def __repr__(self):
        return (f"{self._function.__name__}"
                f"({', '.join(repr(inp) for inp in self._inputs)})")

    def run(self, space: Dict[str, Any], prev: Any) -> Any:
        return self._function(*(inp.run(space, prev) for inp in self._inputs))


class Variable(Apply):
    def __init__(self, name: str):
        super().__init__()
        self._name = name

    def __repr__(self):
        return self._name

    @property
    def name(self) -> str:
        return self._name

    def run(self, space: Dict[str, Any], prev: Any) -> Any:
        return space[self._name]

    def __getattr__(self, item: str) -> Apply:
        return _ApplyFunction(getattr, self, Constant(item))

    def __call__(self, *args, **kwargs) -> Apply:
        pass

    def __mul__(self, other) -> Apply:
        return _ApplyFunction(operator.mul, self, other)

    def __add__(self, other) -> Apply:
        return _ApplyFunction(operator.add, self, other)

    def __pow__(self, power, modulo=None) -> Apply:
        return _ApplyFunction(operator.pow, self, power)

    def __neg__(self) -> Apply:
        return _ApplyFunction(operator.neg, self)

    def __rmul__(self, other) -> Apply:
        return self.__mul__(other)

    def __radd__(self, other) -> Apply:
        return self.__add__(other)


class ApplySet(Apply):
    def __init__(self, variable: Variable, expression: Apply):
        super().__init__()
        self._variable = variable
        self._expression = _wrap(expression)

    def __repr__(self):
        return f"{self._variable} = {self._expression}"

    def run(self, space: Dict[str, Any], prev: Any) -> Any:
        space[self._variable.name] = self._expression.run(space, prev)


class ApplyReturn(Apply):
    def __init__(self, expression: Apply):
        super().__init__()
        self._ret = _wrap(expression)

    def __repr__(self):
        return f"return {self._ret}"

    def run(self, space: Dict[str, Any], prev: Any) -> Any:
        return self._ret.run(space, prev)


class Executor:
    def set(self, variable: Variable, expression: Apply) -> Apply:
        return ApplySet(variable, expression)

    def return_(self, expression: Apply) -> Apply:
        return ApplyReturn(expression)


E = Executor()


class VariableFactory:
    def __getattr__(self, item) -> Variable:
        return Variable(item)


V = VariableFactory()


class Lambda:
    def __init__(self, arguments: Union[Variable, Tuple[Variable, ...]], body: Iterable[Apply]):
        if isinstance(arguments, Variable):
            arguments = (arguments,)
        else:
            assert isinstance(arguments, tuple)
            for argument in arguments:
                assert isinstance(argument, Variable)
        assert len(set(arg.name for arg in arguments)) == len(arguments)

        if isinstance(body, set):
            body = sorted(body, key=lambda apply: apply.order)
        else:
            body = list(body)

        self._arguments: Tuple[Variable, ...] = arguments
        self._body: List[Apply] = body

    def __call__(self, *args):
        if len(args) != len(self._arguments):
            raise RuntimeError(f"Expected {len(self._arguments)} arguments, got {len(args)}")
        space = {
            variable.name: args[i]
            for i, variable in enumerate(self._arguments)
        }
        ret = None
        for apply in self._body:
            print(apply)
            ret = apply.run(space, ret)
        return ret


def main():
    function = Lambda(V.x, {
        E.set(V.y, 2 * V.x),
        E.set(V.z, V.x ** V.y),
        E.return_(-V.z),
    })
    print(function(2))

    f = Lambda((V.x, V.y), [V.x + V.y])
    print(f(4, 5))

    f = Lambda(V.s, [V.s.strip])
    print(f("hello"))


if __name__ == '__main__':
    main()
