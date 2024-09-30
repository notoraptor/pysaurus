from wip.symthon.symthon import E, Lambda, V


def test_return():
    function = Lambda(
        V.x, [E.set(V.y, 2 * V.x), E.set(V.z, V.x**V.y), E.return_(-V.z)]
    )
    assert function(2) == -16


def test_default_return():
    f = Lambda((V.x, V.y), [V.x + V.y])
    assert (f(4, 5)) == 9


def test_getattr_and_call():
    f = Lambda(V.s, [V.s.strip("h") * 2])
    assert (f("hello    ")) == "ello    ello    "


def test_return_constant():
    f = Lambda((), [2])
    assert f() == 2


def test_add():
    f = Lambda(V.x, [V.x + 1])
    assert f(0) == 1
    assert f(1) == 2

    g = Lambda(V.x, [1 + V.x])
    assert g(0) == 1
    assert g(1) == 2


def test_sub():
    f = Lambda(V.x, [V.x - 1])
    assert f(0) == -1
    assert f(1) == 0
    assert f(6) == 5
    assert f(-2) == -3

    g = Lambda(V.x, [1 - V.x])
    assert g(0) == 1
    assert g(1) == 0
    assert g(6) == -5


def test_mul():
    f = Lambda(V.x, [V.x * 4.5])
    assert f(0) == 0
    assert f(1) == 4.5
    assert f(2) == 9.0

    g = Lambda(V.x, [-1.5 * V.x])
    assert g(0) == 0
    assert g(1) == -1.5
    assert g(-2.2) == -1.5 * -2.2


def test_truediv():
    f = Lambda(V.x, [V.x / 2])
    assert f(0) == 0
    assert f(1) == 0.5
    assert f(4.5) == 2.25

    g = Lambda(V.x, [1 / V.x])
    assert g(1) == 1
    assert g(2) == 0.5
    assert g(-3) == -1 / 3


def test_floordiv():
    f = Lambda(V.x, [V.x // 2])
    assert f(0) == 0
    assert f(1) == 0
    assert f(7) == 3

    g = Lambda(V.x, [100 // V.x])
    assert g(1) == 100
    assert g(2) == 50
    assert g(3) == 33


def test_mod():
    f = Lambda((V.x, V.y), [V.x % (1 + V.y)])
    assert f(10, 3) == 10 % 4
    assert f(5, 2) == 5 % 3

    g = Lambda(V.x, [34 % V.x])
    assert g(1) == 0
    assert g(2) == 0
    assert g(3) == 1
    assert g(5) == 4


def test_pow():
    f = Lambda(V.x, [V.x**2.1])
    assert f(0) == 0
    assert f(1) == 1
    assert f(5) == 5**2.1
    assert f(-1.3) == (-1.3) ** 2.1

    g = Lambda(V.x, [2.5**V.x])
    assert g(0) == 1
    assert g(2) == 2.5 * 2.5
    assert g(-5.41) == 2.5 ** (-5.41)


def test_binary_boolean_operators():
    feq = Lambda((V.x, V.y), [V.x == V.y])
    assert feq(2, 2) is True
    assert feq(1, 2) is False

    fne = Lambda((V.x, V.y), [V.x != V.y])
    assert fne(2, 2) is False
    assert fne(1, 2) is True

    flt = Lambda((V.x, V.y), [V.x < V.y])
    assert flt(2, 2) is False
    assert flt(2, 1) is False
    assert flt(1, 2) is True

    fgt = Lambda((V.x, V.y), [V.x > V.y])
    assert fgt(2, 2) is False
    assert fgt(2, 1) is True
    assert fgt(1, 2) is False

    fle = Lambda((V.x, V.y), [V.x <= V.y])
    assert fle(2, 2) is True
    assert fle(2, 1) is False
    assert fle(1, 2) is True

    fge = Lambda((V.x, V.y), [V.x >= V.y])
    assert fge(2, 2) is True
    assert fge(2, 1) is True
    assert fge(1, 2) is False


def test_bitwise_and():
    f = Lambda(V.x, [V.x & 2])
    assert f(0) == 0
    assert f(1) == 0
    assert f(2) == 2
    assert f(3) == 2

    f = Lambda((V.x), [2 & V.x])
    assert f(0) == 0
    assert f(1) == 0
    assert f(2) == 2
    assert f(3) == 2


def test_bitwise_or():
    f = Lambda(V.x, [V.x | 2])
    assert f(0) == 2
    assert f(1) == 3
    assert f(2) == 2
    assert f(3) == 3

    f = Lambda((V.x), [2 | V.x])
    assert f(0) == 2
    assert f(1) == 3
    assert f(2) == 2
    assert f(3) == 3


def test_bitwise_xor():
    f = Lambda(V.x, [V.x ^ 2])
    assert f(0) == 2
    assert f(1) == 3
    assert f(2) == 0
    assert f(3) == 1

    f = Lambda((V.x), [2 ^ V.x])
    assert f(0) == 2
    assert f(1) == 3
    assert f(2) == 0
    assert f(3) == 1


def test_bitwise_lshift():
    f = Lambda(V.x, [V.x << 2])
    assert f(0) == 0
    assert f(1) == 4
    assert f(2) == 8
    assert f(3) == 0b1100

    f = Lambda((V.x), [2 << V.x])
    assert f(0) == 2
    assert f(1) == 4
    assert f(2) == 8
    assert f(3) == 16


def test_bitwise_rshift():
    f = Lambda(V.x, [V.x >> 2])
    assert f(0) == 0
    assert f(1) == 0
    assert f(2) == 0
    assert f(0b1100) == 0b11
    assert f(0b1100101) == 0b11001

    f = Lambda((V.x), [2 >> V.x])
    assert f(0) == 2
    assert f(1) == 1
    assert f(2) == 0


def test_bitwise_inv():
    f = Lambda(V.x, [~V.x])
    assert f(0) == ~0
    assert f(1) == ~1
    assert f(2) == ~2
    assert f(3) == ~3
    assert f(4) == ~4


def test_abs():
    f = Lambda(V.x, [abs(V.x)])
    assert f(12) == 12
    assert f(-12) == 12


def test_neg_and_abs():
    f = Lambda(V.x, [-V.x])
    assert f(2) == -2
    assert f(-2) == 2

    g = Lambda(V.x, [+V.x])
    assert g(2) == 2
    assert g(-2) == -2


def test_and_or_not():
    not_ = Lambda(V.x, [E.not_(V.x)])
    assert not not_(1)
    assert not_(0)

    and_ = Lambda((V.x, V.y), [E.and_(V.x, V.y)])
    assert and_(1, 2) == 2
    assert and_(0, 1) == 0

    or_ = Lambda((V.x, V.y), [E.or_(V.x, V.y)])
    assert or_(1, 2) == 1
    assert or_(0, 5) == 5
    assert or_(0, 0) == 0
    assert or_(0, False) is False


def test_getattr_setattr_call():
    class A:
        def __init__(self):
            self.x = 10

        def thing(self):
            return self.x + 1

    a = A()
    f = Lambda((), [E.set(V[a].x, V[a].x + 1), V[a].thing()])
    assert f() == 12
    assert a.x == 11

    b = A()
    b.x = a
    g = Lambda((), [E.set(V[b].x.x, 2.5 * V[a].x)])
    assert g() is None
    assert a.x == 27.5


def test_if():
    f = Lambda(V.x, [E.if_(V.x, [E.return_("hello")]), "world"])
    assert f(True) == "hello"
    assert f(False) == "world"


def test_if_else():
    f = Lambda(
        V.x, [E.if_(V.x == 1, [E.return_("is one")]).else_(E.return_("not one"))]
    )
    assert f(1) == "is one"
    assert f(2) == "not one"


def test_if_elif_else():
    f = Lambda(
        (V.x, V.y),
        [
            E.if_(V.x == V.y, [E.set(V.z, V.x + V.y + 0.5), E.return_(V.z)])
            .elif_(V.x > V.y, [E.return_(V.x * V.y)])
            .elif_(V.x < V.y / 2, [E.set(V.w, "what")])
            .else_(E.set(V.w, "else")),
            V.w,
        ],
    )

    assert f(1, 1) == 2.5
    assert f(3, 2) == 6
    assert f(5, 11) == "what"
    assert f(1, 2) == "else"


def test_range():
    f = Lambda(V.x, [V[list](E.range(V.x))])
    assert f(5) == [0, 1, 2, 3, 4]
