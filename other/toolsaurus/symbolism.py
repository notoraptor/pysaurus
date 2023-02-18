import operator
from abc import abstractmethod

from pysaurus.core.functions import indent_string_tree


def _and_(a, b):
    return a and b


def _or_(a, b):
    return a or b


def _identity_(a):
    return a


class Run:
    __slots__ = ("__children__",)

    def __init__(self, *children):
        self.__children__ = list(children)

    def __inline__(self, nest=True, select=None):
        children = []
        for element in self.__children__:
            if select is None or select(self, element):
                if isinstance(element, Run):
                    children.extend(element.__inline__(nest=nest, select=select))
                else:
                    children.append(element)
        return [self, children] if nest else [self] + children

    def __apply__(self, function: callable):
        function(self)
        for element in self.__children__:
            if isinstance(element, Run):
                element.__apply__(function)
            else:
                function(element)

    def __pretty__(self, select=None, indentation="\t"):
        return indent_string_tree(
            self.__inline__(nest=True, select=select), indentation=indentation
        )

    @abstractmethod
    def __run__(self, **kwargs):
        pass

    def __call__(self, **kwargs):
        return self.__run__(**kwargs)


class _Raw(Run):
    __slots__ = ()

    def __init__(self, value):
        super().__init__(value)

    def __str__(self):
        return repr(self.__children__[0])

    def __run__(self, **kwargs):
        return self.__children__[0]

    def __inline__(self, select=None, nest=True):
        return [self]


class _Apply(Run):
    __slots__ = ()

    def __init__(self, fn, *inputs):
        super().__init__(
            fn, *(inp if isinstance(inp, Run) else _Raw(inp) for inp in inputs)
        )

    def __str__(self):
        return f"{self.__children__[0].__name__}()"

    def __run__(self, **kwargs):
        return self.__children__[0](
            *(inp.__run__(**kwargs) for inp in self.__children__[1:])
        )

    def __eq__(self, other):
        return _Apply(operator.eq, self, other)

    def __ne__(self, other):
        return _Apply(operator.ne, self, other)

    def __lt__(self, other):
        return _Apply(operator.lt, self, other)

    def __gt__(self, other):
        return _Apply(operator.gt, self, other)

    def __le__(self, other):
        return _Apply(operator.le, self, other)

    def __ge__(self, other):
        return _Apply(operator.ge, self, other)

    def __and__(self, other):
        return _And(self, other)

    def __or__(self, other):
        return _Or(self, other)

    def __invert__(self):
        return _Apply(operator.not_, self)

    def __len__(self):
        return _Apply(len, self)

    def __abs__(self):
        return _Apply(abs, self)

    def __getitem__(self, item_):
        return _Apply(operator.getitem, self, item_)

    def __getattr__(self, item_):
        return _Apply(getattr, self, item_)


class _And(_Apply):
    def __init__(self, a, b):
        super().__init__(_and_, a, b)

    def __run__(self, **kwargs):
        node_a, node_b = self.__children__[1:]
        return node_a.__run__(**kwargs) and node_b.__run__(**kwargs)


class _Or(_Apply):
    def __init__(self, a, b):
        super().__init__(_or_, a, b)

    def __run__(self, **kwargs):
        node_a, node_b = self.__children__[1:]
        return node_a.__run__(**kwargs) or node_b.__run__(**kwargs)


class Object(_Apply):
    __slots__ = ()

    def __init__(self, value):
        super().__init__(_identity_, value)

    def __str__(self):
        child = self.__children__[1]
        return str(child) if isinstance(child, Run) else repr(child)

    def __inline__(self, select=None, nest=True):
        return [self]


class _Feed(_Apply):
    __slots__ = ()

    def __init__(self, fn: callable, source_name: str, element_name: str):
        super().__init__(fn, source_name, element_name)

    def __run__(self, **kwargs):
        fn = self.__children__[0]
        source_name = self.__children__[1].__children__[0]
        name = self.__children__[2].__children__[0]
        if source_name not in kwargs:
            raise ValueError(f'Required argument "{source_name}" for condition')
        source = kwargs[source_name]
        return fn(source, name)


def pretty(cond: Run, indentation="  "):
    def select(parent, child):
        if isinstance(parent, _Apply) and parent.__children__[0] is child:
            return False
        return True

    return cond.__pretty__(select=select, indentation=indentation)


def attr(name: str) -> _Feed:
    return _Feed(getattr, "attributes", name)


def item(name: str) -> _Feed:
    return _Feed(operator.getitem, "items", name)
