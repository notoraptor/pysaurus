def unpack_args(function):
    """
    Wraps a function with multiple args into a function with a tuple as args.

    Decorator to wrap a function that receives multiple arguments f(*args)
    into a function that receives only a sequence of arguments g(args)
    """

    def wrapper(args):
        return function(*args)

    wrapper.__name__ = function.__name__

    return wrapper


@unpack_args
def f(a, b, c):
    return a * b + c


def test_unpack_args():
    args = (2, 3, 4)
    assert f(args) == 10
