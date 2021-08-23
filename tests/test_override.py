from pysaurus.core.override import Override

f = Override("f")


@f.override
def f():
    return 0


@f.override
def f(x: int):
    return 2 * x


class A:
    __init__ = Override("A.__init__")

    @__init__.override
    def __init__(self):
        self.a = 2

    @__init__.override
    def __int__(self, a: int):
        self.a = a

    f = Override("A.f")

    @f.override
    def f(self):
        return self.a

    @f.override
    def f(self, x: int):
        return self.a * x

    @f.override
    def f(self, x: object):
        return "object"


class B(A):
    @A.f.override
    def f(self):
        return -1

    @A.f.override
    def f(self, x: float):
        return -1

    @A.f.override
    def f(self, x: object):
        return f"type is {type(x).__name__}"


def test_f():
    assert f() == 0
    assert f(3) == 6


def test_B():
    b = B()
    assert b.f() == -1
    assert b.f(1.0) == -1
    assert b.f(3) == 6
    assert b.f(None) == "type is NoneType"


def test_A():
    a = A(100)
    assert a.f() == 100
    assert a.f(3) == 300
    assert a.f("tata") == "object"
