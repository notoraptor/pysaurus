from other.toolsaurus.symbolism import Object, attr, item, pretty


class A:
    def __init__(self):
        self.a = 1
        self.b = 2
        self.c = 3
        self.d = dict(x=1, y=2)

    def __str__(self):
        return f"A(a={self.a}, b={self.b}, c={self.c}, d={self.d})"

    __repr__ = __str__


def test_symbolism():
    obj_a = A()
    a = Object(obj_a)
    cond = (a.a == -2) | (2 > a.a)
    assert (
        pretty(cond)
        == """
_or_()
  eq()
    getattr()
      A(a=1, b=2, c=3, d={'x': 1, 'y': 2})
      'a'
    -2
  lt()
    getattr()
      A(a=1, b=2, c=3, d={'x': 1, 'y': 2})
      'a'
    2
""".strip()
    )
    assert cond()

    test = (attr("b") < 3) & (item("y") == 1)
    assert (
        pretty(test)
        == """
_and_()
  lt()
    getattr()
      'attributes'
      'b'
    3
  eq()
    getitem()
      'items'
      'y'
    1
""".strip()
    )
    assert not test(attributes=obj_a, items=obj_a.d)
    d = dict(y=1)
    assert test(attributes=obj_a, items=d)


test_symbolism()
