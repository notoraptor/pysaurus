from pysaurus.core.functions import unpack_args


@unpack_args
def f(a, b, c):
    return a * b + c


def test_unpack_args():
    args = (2, 3, 4)
    assert f(args) == 10
