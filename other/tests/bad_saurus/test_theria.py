from other.bad_saurus.gui import theria


class A:
    def __init__(self):
        self.x = 0
        self.a = 2
        self.z = -1
        self.d = 12

    def f2(self):
        pass

    def f1(self):
        pass


class B:
    __slots__ = ("x", "a", "d", "z")

    def __init__(self):
        self.x = 0
        self.a = 2
        self.z = -1
        self.d = 12


def test_get_structure():
    assert theria.get_structure(A()) == (("x", "a", "z", "d"), ("f2", "f1"))
    assert theria.get_structure(B()) == (("x", "a", "d", "z"), ())
