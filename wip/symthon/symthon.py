import operator
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Self, Sequence, Tuple, Union

from pysaurus.core import functions


def _assert_str(value) -> str:
    assert isinstance(value, str)
    return value


def _name_of(something):
    if isinstance(something, Variable):
        return repr(something)
    if hasattr(something, "__qualname__"):
        return something.__qualname__
    if hasattr(something, "__name__"):
        return something.__name__
    return repr(something)


class _Stopped:
    __slots__ = ("value",)

    def __init__(self, value=None):
        self.value = value

    def __bool__(self):
        return True


class _Continued(_Stopped):
    __slots__ = ()


class _Broken(_Stopped):
    __slots__ = ()


class _Returned(_Stopped):
    __slots__ = ()


class Variable(ABC):
    __slots__ = ()

    def __repr__(self):
        return type(self).__name__

    @abstractmethod
    def __run__(self, space: Dict[str, Any]) -> Any:
        raise NotImplementedError()

    def __getattr__(self, item) -> Self:
        return Getattr(self, item)

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
        return Function(operator.add, other, self)

    def __rsub__(self, other) -> Self:
        return Function(operator.add, -self, other)

    def __rmul__(self, other) -> Self:
        return Function(operator.mul, other, self)

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

    @classmethod
    def _wrap(cls, something) -> Self:
        return something if isinstance(something, Variable) else Value(something)


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

    def __run__(self, space: Dict[str, Any]) -> Any:
        return space[self._name]


class Value(Variable):
    __slots__ = ("_value",)

    def __init__(self, value):
        super().__init__()
        self._value = value

    def __repr__(self):
        return _name_of(self._value)

    def __run__(self, space: Dict[str, Any]) -> Any:
        return self._value


class _Expression(Variable):
    __slots__ = ()


class Function(_Expression):
    __slots__ = ("_function", "_args", "_kwargs")

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self._function = self._wrap(function)
        self._args = [self._wrap(arg) for arg in args]
        self._kwargs = {
            _assert_str(key): self._wrap(value) for key, value in kwargs.items()
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

    def __run__(self, space: Dict[str, Any]) -> Any:
        return (self._function.__run__(space))(
            *(arg.__run__(space) for arg in self._args),
            **{key: value.__run__(space) for key, value in self._kwargs.items()},
        )


class Getattr(Function):
    __slots__ = ()

    def __init__(self, obj, name):
        super().__init__(getattr, obj, name)

    @property
    def obj(self) -> Variable:
        return self._args[0]

    @property
    def name(self) -> Variable:
        return self._args[1]


class Assign(_Expression):
    __slots__ = ("_lvalue", "_rvalue")

    def __init__(self, lvalue: Union[Reference, Getattr], rvalue: Variable):
        lvalue = self._wrap(lvalue)
        rvalue = self._wrap(rvalue)
        assert isinstance(lvalue, (Getattr, Reference))
        super().__init__()
        self._lvalue = lvalue
        self._rvalue = rvalue

    def __run__(self, space: Dict[str, Any]) -> Any:
        rvalue = self._rvalue.__run__(space)
        if isinstance(self._lvalue, Reference):
            space[self._lvalue.name] = rvalue
        else:
            assert isinstance(self._lvalue, Getattr)
            attribute_path = []
            curr = self._lvalue
            while True:
                attribute_path.append(curr.name)
                obj = curr.obj
                if isinstance(obj, Getattr):
                    curr = obj
                else:
                    origin = obj
                    break
            base = origin.__run__(space)
            *prev_paths, last_path = [
                _assert_str(name.__run__(space)) for name in reversed(attribute_path)
            ]
            for key in prev_paths:
                base = getattr(base, key)
            setattr(base, last_path, rvalue)


class Return(_Expression):
    __slots__ = ("_ret",)

    def __init__(self, ret: Variable):
        super().__init__()
        self._ret = self._wrap(ret)

    def __run__(self, space: Dict[str, Any]) -> Any:
        return _Returned(self._ret.__run__(space))


class Block(_Expression):
    __slots__ = ("_block", "_stop_cls")

    def __init__(self, block: Sequence[_Expression], stop_only_on_returns=False):
        super().__init__()
        self._block = [self._wrap(expr) for expr in block]
        self._stop_cls = _Returned if stop_only_on_returns else _Stopped

    def __run__(self, space: Dict[str, Any]) -> Any:
        ret = None
        for variable in self._block:
            ret = variable.__run__(space)
            if isinstance(ret, self._stop_cls):
                return ret
        return ret


class If(_Expression):
    __slots__ = ("_condition", "_block")

    def __init__(self, condition: Variable, block: Sequence[_Expression]):
        super().__init__()
        self._condition = self._wrap(condition)
        self._block = Block(block)

    def __run__(self, space: Dict[str, Any]) -> Union[bool, _Stopped]:
        if self._condition.__run__(space):
            ret = self._block.__run__(space)
            return ret if isinstance(ret, _Stopped) else True
        else:
            return False

    def elif_(self, condition: Variable, block: Sequence[_Expression]):
        return Elif(self, condition, block)

    def else_(self, *block: _Expression):
        return Else(self, block)


class Elif(If):
    __slots__ = ("_from_if",)

    def __init__(self, from_if: If, condition: Variable, block: Sequence[_Expression]):
        super().__init__(condition, block)
        self._from_if = from_if

    def __run__(self, space: Dict[str, Any]) -> Union[bool, _Stopped]:
        return self._from_if.__run__(space) or super().__run__(space)


class Else(_Expression):
    __slots__ = ("_from_if", "_block")

    def __init__(self, from_if: If, block: Sequence[_Expression]):
        super().__init__()
        self._from_if = from_if
        self._block = Block(block)

    def __run__(self, space: Dict[str, Any]) -> Union[bool, _Stopped]:
        ret_if = self._from_if.__run__(space)
        if ret_if:
            return ret_if
        else:
            ret = self._block.__run__(space)
            return ret if isinstance(ret, _Stopped) else True


class _Loop(_Expression):
    __slots__ = ()

    @abstractmethod
    def __run__(self, space: Dict[str, Any]) -> Optional[_Stopped]:
        raise NotImplementedError()


class For(_Loop):
    __slots__ = ("_statement", "_iterable", "_block", "_parse_data")

    def __init__(
        self,
        statement: Union[Reference, Tuple[Reference, ...]],
        iterable: Variable,
        block: Sequence[_Expression],
    ):
        if isinstance(statement, Reference):
            _parse_data = self._data_to_one_statement
        else:
            assert isinstance(statement, tuple)
            assert all(isinstance(ref, Reference) for ref in statement)
            _parse_data = self._data_to_many_statements
        super().__init__()
        self._statement = statement
        self._iterable = self._wrap(iterable)
        self._block = Block(block)
        self._parse_data = _parse_data

    def _data_to_one_statement(self, data, space: Dict[str, Any]):
        space[self._statement.name] = data

    def _data_to_many_statements(self, data: tuple, space: Dict[str, Any]):
        for i, ref in enumerate(self._statement):
            space[ref.name] = data[i]

    def __run__(self, space: Dict[str, Any]) -> Optional[_Stopped]:
        for data in self._iterable.__run__(space):
            self._parse_data(data, space)
            ret = self._block.__run__(space)
            if isinstance(ret, _Stopped):
                if type(ret) is _Continued:
                    continue
                else:
                    return ret
        return None

    def else_(self, *block: _Expression):
        return _ForElse(self, block)


class _ForElse(_Expression):
    __slots__ = ("_for", "_block")

    def __init__(self, from_for: _Loop, block: Sequence[_Expression]):
        super().__init__()
        self._for = from_for
        self._block = Block(block)

    def __run__(self, space: Dict[str, Any]) -> Any:
        ret_for = self._for.__run__(space)
        if ret_for is None:
            ret_for = self._block.__run__(space)
        return ret_for if isinstance(ret_for, _Stopped) else False


class Continue(_Expression):
    __slots__ = ()

    def __run__(self, space: Dict[str, Any]) -> Any:
        return _Continued()


class Break(_Expression):
    __slots__ = ()

    def __run__(self, space: Dict[str, Any]) -> Any:
        return _Broken()


class While(_Loop):
    __slots__ = ("_condition", "_block")

    def __init__(self, condition: Variable, block: Sequence[_Expression]):
        super().__init__()
        self._condition = self._wrap(condition)
        self._block = Block(block)

    def __run__(self, space: Dict[str, Any]) -> Optional[_Stopped]:
        while True:
            condition = self._condition.__run__(space)
            if condition:
                ret = self._block.__run__(space)
                if isinstance(ret, _Stopped):
                    if type(ret) is _Continued:
                        continue
                    else:
                        return ret
            else:
                break
        return None

    def else_(self, *block: _Expression) -> _ForElse:
        return _ForElse(self, block)


class With(_Expression):
    __slots__ = ("_expr", "_as", "_block")

    def __init__(
        self,
        expr: _Expression,
        as_or_block: Union[Reference, Sequence[_Expression]],
        block: Optional[Sequence[_Expression]] = None,
    ):
        if block is None:
            as_ = None
            block = as_or_block
        else:
            as_ = as_or_block

        if as_ is not None:
            assert isinstance(as_, Reference)

        super().__init__()
        self._expr = self._wrap(expr)
        self._as = as_
        self._block = Block(block)

    def __run__(self, space: Dict[str, Any]) -> Any:
        with self._expr.__run__(space) as context:
            if self._as is not None:
                space[self._as.name] = context
            return self._block.__run__(space)


class Condition(_Expression):
    __slots__ = ["_condition", "_if_true", "_if_false"]

    def __init__(self, condition: Variable, if_true: Variable, if_false: Variable):
        super().__init__()
        self._condition = self._wrap(condition)
        self._if_true = self._wrap(if_true)
        self._if_false = self._wrap(if_false)

    def __run__(self, space: Dict[str, Any]) -> Any:
        return (
            self._if_true.__run__(space)
            if self._condition.__run__(space)
            else self._if_false.__run__(space)
        )


class MetaLambda(type):
    def __getitem__(self, block):
        if not isinstance(block, tuple):
            block = (block,)
        return self(None, block)


class Lambda(metaclass=MetaLambda):
    __slots__ = ("_arguments", "_body")

    def __init__(
        self,
        arguments: Optional[Union[Reference, Tuple[Reference, ...]]],
        body: Sequence[_Expression],
    ):
        if arguments is not None:
            if isinstance(arguments, Reference):
                arguments = (arguments,)
            else:
                assert isinstance(arguments, tuple)
                for argument in arguments:
                    assert isinstance(argument, Reference)
            if len(set(arg.name for arg in arguments)) != len(arguments):
                raise RuntimeError("Duplicate argument name")

        self._arguments: Optional[Tuple[Reference, ...]] = arguments
        self._body = Block(body, stop_only_on_returns=True)

    def __call__(self, *args):
        if self._arguments is None:
            space = {}
        else:
            if len(args) != len(self._arguments):
                raise RuntimeError(
                    f"Expected {len(self._arguments)} arguments, got {len(args)}"
                )
            space = {ref.name: args[i] for i, ref in enumerate(self._arguments)}
        ret = self._body.__run__(space)
        return ret.value if isinstance(ret, _Returned) else ret


class ReferenceFactory:
    def __getattr__(self, item: str) -> Reference:
        return Reference(item)

    def __getitem__(self, item) -> Value:
        assert not isinstance(item, Variable)
        return Value(item)


class ExpressionFactory:
    @classmethod
    def set(
        cls, reference: Union[Reference, Getattr], variable: Variable
    ) -> _Expression:
        return Assign(reference, variable)

    @classmethod
    def setattr(cls, element, **kwargs) -> Block:
        return Block(
            [Assign(Getattr(element, key), value) for key, value in kwargs.items()]
        )

    @classmethod
    def and_(cls, a: Variable, b: Variable) -> Function:
        return Function(functions.boolean_and, a, b)

    @classmethod
    def or_(cls, a: Variable, b: Variable) -> Function:
        return Function(functions.boolean_or, a, b)

    @classmethod
    def not_(cls, variable: Variable) -> Function:
        return Function(operator.not_, variable)

    if_ = If
    for_ = For
    while_ = While
    continue_ = Continue
    break_ = Break
    return_ = Return
    with_ = With
    cond = Condition

    @classmethod
    def range(cls, start, stop=None, step=1) -> Variable:
        if stop is None:
            start, stop = 0, start
        return Value(range)(start, stop, step)

    @classmethod
    def print(cls, *args, **kwargs) -> Variable:
        return Value(print)(*args, **kwargs)


V = ReferenceFactory()
E = ExpressionFactory()
