class A(int):
    def __bool__(self):
        return True


def test_integer_presence():
    assert 0 or 1 == 1
    assert A(0) or 1 == 0
    assert None or A(0) == 0
