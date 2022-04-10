from other.toolsaurus.override import override


def f():
    return ""


@override
def f(val: int):
    return f"f:int:{val}"


class A:
    x = 3

    def h(self):
        return f"{type(self).__name__}.h"

    def g(self):
        return f"{type(self).__name__}.g"

    @override
    def g(self, x: int):
        return f"{type(self).__name__}.g:int:{x}"


class B(A):
    @override(A)
    def g(self, y: float):
        return f"{type(self).__name__}.g:float:{y}"

    @override(A)
    def h(self, x: object):
        return f"{type(self).__name__}.h:object:{x}"


def test():
    assert f() == ""
    assert f(12) == "f:int:12"
    a = A()
    assert a.g() == "A.g"
    assert a.g(12) == "A.g:int:12"
    b = B()
    assert b.g() == "B.g"
    assert b.g(2) == "B.g:int:2"
    assert b.g(2.3) == "B.g:float:2.3"
    assert b.h() == "B.h"
    assert b.h(-1) == "B.h:object:-1"
