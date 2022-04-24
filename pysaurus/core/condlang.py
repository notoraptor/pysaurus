import ast
import operator
from abc import abstractmethod
from typing import List


def _in_(a, b):
    return operator.contains(b, a)


def _not_in_(a, b):
    return not operator.contains(b, a)


__binary_operations__ = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
    ast.BitOr: operator.or_,
    ast.BitXor: operator.xor,
    ast.BitAnd: operator.and_,
    ast.MatMult: operator.matmul,
}

__unary_operations__ = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
    ast.Invert: operator.inv,
}

__cmp_operations__ = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
    ast.In: _in_,
    ast.NotIn: _not_in_,
}


class Run:
    __slots__ = ("runs",)

    def __init__(self, *runs):
        self.runs: List[Run] = list(runs)

    def __str__(self):
        return type(self).__name__

    @staticmethod
    def __pretty__(run, prefix="") -> str:
        output = f"{prefix}{run}"
        for child in run.runs:
            output += "\n" + Run.__pretty__(child, prefix=f"{prefix}\t")
        return output

    def pretty(self):
        return self.__pretty__(self)

    @abstractmethod
    def run(self, **kwargs):
        pass

    def __call__(self, **kwargs):
        return self.run(**kwargs)


class Function(Run):
    __slots__ = ("function",)

    def __init__(self, function, *inputs):
        super().__init__(*inputs)
        self.function = function

    def __str__(self):
        return f"Function:{self.function.__name__}"

    def run(self, **kwargs):
        return self.function(*(run.run(**kwargs) for run in self.runs))


class And(Run):
    __slots__ = ()

    def run(self, **kwargs):
        value = True
        for run in self.runs:
            value = run.run(**kwargs)
            if not value:
                return False
        return value


class Or(Run):
    __slots__ = ()

    def run(self, **kwargs):
        value = False
        for run in self.runs:
            value = run.run(**kwargs)
            if value:
                return value
        return value


class Variable(Run):
    __slots__ = ("name",)

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def __str__(self):
        return f"Variable:{self.name}"

    def run(self, namespace, **kwargs):
        return getattr(namespace, self.name)


class Subscript(Run):
    __slots__ = ()

    def __init__(self, data, item):
        super().__init__(data, item)

    def run(self, **kwargs):
        data, item = self.runs
        return data.run(**kwargs)[item.run(**kwargs)]


class Constant(Run):
    __slots__ = ("value",)

    def __init__(self, value):
        super().__init__()
        self.value = value

    def __str__(self):
        return f"Constant({type(self.value).__name__}):{self.value}"

    def run(self, **kwargs):
        return self.value


def compute_ast(node: ast.AST):
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            run_cls = And
        elif isinstance(node.op, ast.Or):
            run_cls = Or
        else:
            raise ValueError(f"Unknown boolop: {node.op}")
        return run_cls(*(compute_ast(child) for child in node.values))
    elif isinstance(node, ast.BinOp):
        op = type(node.op)
        if op not in __binary_operations__:
            raise ValueError(f"Unknown binop: {node.op}")
        return Function(
            __binary_operations__[op], compute_ast(node.left), compute_ast(node.right)
        )
    elif isinstance(node, ast.UnaryOp):
        op = type(node.op)
        if op not in __unary_operations__:
            raise ValueError(f"Unknown unary op: {node.op}")
        return Function(__unary_operations__[op], compute_ast(node.operand))
    elif isinstance(node, ast.Compare):
        if len(node.ops) != 1:
            raise ValueError("Chained comparisons not supported")
        op = type(node.ops[0])
        if op not in __cmp_operations__:
            raise ValueError(f"Unknown cmpop: {node.ops[0]}")
        return Function(
            __cmp_operations__[op],
            compute_ast(node.left),
            compute_ast(node.comparators[0]),
        )
    elif isinstance(node, ast.Name):
        if not isinstance(node.ctx, ast.Load):
            raise ValueError(
                f"Only readonly ast names supported, got: {ast.dump(node)}"
            )
        return Variable(node.id)
    elif isinstance(node, ast.Constant):
        return Constant(node.value)
    elif isinstance(node, ast.Subscript):
        if not isinstance(node.ctx, ast.Load):
            raise ValueError(
                f"Only readonly ast subscripts supported, got {ast.dump(node)}"
            )
        return Subscript(compute_ast(node.value), compute_ast(node.slice))
    elif isinstance(node, ast.Index):
        return compute_ast(node.value)
    elif isinstance(node, ast.Call):
        if not (
            isinstance(node.func, ast.Name) and isinstance(node.func.ctx, ast.Load)
        ):
            raise ValueError(
                f"Ast call supported for readonly function name, got {ast.dump(node)}"
            )
        name = node.func.id
        if name.lower() not in ("len", "count"):
            raise ValueError(
                f"Only len() function call supported, got: {ast.dump(node)}"
            )
        if not (len(node.args) == 1 and len(node.keywords) == 0):
            raise ValueError(
                f"Only len(a) function call supported, got {ast.dump(node)}"
            )
        return Function(len, compute_ast(node.args[0]))
    else:
        raise ValueError(f"Unsupported ast: {ast.dump(node)}")


def cond_lang(code: str) -> Run:
    syntax = ast.parse(code)
    assert len(syntax.body) == 1
    (body,) = syntax.body
    assert isinstance(body, ast.Expr)
    return compute_ast(body.value)


__all__ = ["cond_lang"]
