import pytest

from pysaurus.core.jsonable import Jsonable, Type


class A(Jsonable):
    x: float
    a = 5
    y: str
    b: float = 3.3


class B(A):
    a = -1.0
    e = True
    z = [1, 2]


class B2(Jsonable):
    pass


class B3(Jsonable):
    m = -5
    __short__ = {"m": "holala"}


class C(Jsonable):
    a: int
    c: A
    b = 2
    f = 1
    e: B2 = {}
    d = B3(m=-4)
    g: B3 = {"holala": 100}


class D(Jsonable):
    y: int = None
    a: A = None


class E(Jsonable):
    __slots__ = ("other",)
    t = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.other = -22


def test_jsonable():
    a = A(x=0.0, y="")
    b = B(x=0.0, y="", z=[2])
    b_ = B2()
    c = C(a=0, c=A(x=0.0, y=""))
    assert b.x == 0.0
    assert b.z == [2]
    assert b.__json__["x"] == 0.0
    assert b.__json__["z"] == [2]
    assert b.to_json() is b.__json__
    assert str(a) == "A(a=5, b=3.3, x=0.0, y='')"
    assert str(b) == "B(a=-1.0, b=3.3, e=True, x=0.0, y='', z=[2])"
    assert str(b_) == "B2()"
    assert str(c) == (
        "C(a=0, b=2, c=A(a=5, b=3.3, x=0.0, y=''), d=B3(m=-4), e=B2(), f=1, g=B3(m=100))"
    )
    assert a == A.from_dict(a.to_dict())
    assert b == B.from_dict(b.to_dict())
    assert c == C.from_dict(c.to_dict())


def test_shorten():
    b = B3()
    assert b.m == -5
    assert b.to_dict() == {"holala": -5}
    assert str(b) == "B3(m=-5)"
    assert b == B3.from_dict(b.to_dict())


def test_none():
    assert str(D()) == "D(a=None, y=None)"
    assert str(D(y=None)) == "D(a=None, y=None)"
    assert str(D(y=2)) == "D(a=None, y=2)"
    assert (
        str(D(a={"b": 11.0, "x": 0.0, "y": ""}))
        == "D(a=A(a=5, b=11.0, x=0.0, y=''), y=None)"
    )
    assert (
        str(D(a=A(b=11.0, x=0.0, y=""))) == "D(a=A(a=5, b=11.0, x=0.0, y=''), y=None)"
    )


def test_inherited():
    e = E()
    assert not hasattr(e, "__dict__")
    assert e.other == -22
    assert str(e) == "E(t=0)"


def test_type():
    t = Type("test", int)
    with pytest.raises(ValueError):
        t.new()
    assert t.validate(12) == 12
    assert t.to_dict(10) == 10
    assert str(t) == "test: int"

    t = Type("test", int, 7)
    assert t.new() == 7
    assert t.validate(12) == 12
    assert t.to_dict(10) == 10
    assert str(t) == "test: int = 7"

    t = Type("test", float, 4.9)
    assert t.new() == 4.9
    assert t.validate(5.0) == 5.0
    assert str(t) == "test: float = 4.9"

    t = Type("test", int, 4)
    assert t.new() == 4
    assert t.validate(1) == 1
    assert str(t) == "test: int = 4"

    t = Type("test", (bool, "t"))
    assert str(t) == "test(t): bool"

    t = Type("test", ("t", float), -1.0)
    assert str(t) == "test(t): float = -1.0"

    t = Type("test", "t", None)
    assert str(t) == "test(t): Any = None"
