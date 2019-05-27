from pysaurus.core import errors, utils
from pysaurus.core.property_type import PropertyType


class AssertRaise:

    def __init__(self, exceptions):
        exceptions = tuple(exceptions) if utils.is_iterable(exceptions) else (exceptions,)
        assert exceptions
        self.exceptions = exceptions

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if issubclass(exc_type, self.exceptions):
            print('Raised', exc_type.__name__, exc_val)
            return True
        return False


def test_property():
    with AssertRaise(errors.PropertyNameError):
        PropertyType(name='a b c', property_type=int)
    for name in ('a1_', '_a1', '1a_'):
        PropertyType(name, int)
    p_unique = PropertyType('integer', int, multiple=False)
    p_multiple = PropertyType('integer', int, multiple=True)
    assert p_unique.name == 'integer'
    assert p_unique.default == 0
    assert p_multiple.default == {0}
    assert p_unique.new(33).value == 33
    assert p_multiple.new([44, 44]).value == {44}
    assert p_multiple.new([44, 44, 37]).value == {37, 44}
    v = p_multiple.new([1, 2])
    assert v.value == {1, 2}
    v = p_multiple.add(v, {4, 7})
    assert v.value == {1, 2, 4, 7}
    v = p_multiple.remove(v, [2, 4])
    assert v.value == {1, 7}
    p = PropertyType('a1', float, enumeration=[float(val) for val in range(11)])
    with AssertRaise(Exception):
        p.new(-1.)
    assert p.new(1.).value == 1.
    p.multiple = True
    assert p.new({2.}).value == {2.}
    pj = PropertyType.from_json(p.to_json())
    assert pj == p
    pj.name = 'a2'
    assert pj != p
    assert pj > p


if __name__ == '__main__':
    test_property()
