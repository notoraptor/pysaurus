from pysaurus.core.jsonable import Jsonable


class A(Jsonable):
    x: float
    a = 5
    y: str
    b: int = 3.3


class B(A):
    a = -1.0
    e = True
    z = [1, 2]


class B_(Jsonable):
    pass


class _B(Jsonable):
    m = -5
    __short__ = {"m": "holala"}


class C(Jsonable):
    a: int
    c: A
    b = 2
    f = 1
    e: B_ = {}
    d = _B(m=-4)
    g: _B = {"holala": 100}


class D(Jsonable):
    y: int = None
    a: A = None


def test_jsonable():
    a = A()
    b = B(z=[2])
    b_ = B_()
    c = C()
    assert str(a) == "A(a=5, b=3, x=0.0, y='')"
    assert str(b) == "B(a=-1.0, b=3, e=True, x=0.0, y='', z=[2])"
    assert str(b_) == "B_()"
    assert str(c) == (
        "C(a=0, b=2, c=A(a=5, b=3, x=0.0, y=''), d=_B(m=-4), e=B_(), f=1, g=_B(m=100))"
    )
    assert a == A.from_dict(a.to_dict())
    assert b == B.from_dict(b.to_dict())
    assert c == C.from_dict(c.to_dict())


def test_shorten():
    b = _B()
    assert b.m == -5
    assert b.to_dict() == {"holala": -5}
    assert str(b) == "_B(m=-5)"
    assert b == _B.from_dict(b.to_dict())


def test_none():
    assert str(D()) == "D(a=None, y=None)"
    assert str(D(y=None)) == "D(a=None, y=None)"
    assert str(D(y=2)) == "D(a=None, y=2)"
    assert str(D(a={"b": 11})) == "D(a=A(a=5, b=11, x=0.0, y=''), y=None)"
