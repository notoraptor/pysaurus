from pysaurus.core import functions


def test_function_generate_infinite():
    limited_iterable = range(10)
    infinite_iterable = functions.generate_infinite(-1)
    output = [a * b for a, b in zip(limited_iterable, infinite_iterable)]
    assert output == [0, -1, -2, -3, -4, -5, -6, -7, -8, -9]


def test_sub_exceptions():
    from pysaurus.core.core_exceptions import ApplicationError
    from pysaurus.application.exceptions import PysaurusError

    assert issubclass(ApplicationError, Exception)
    assert issubclass(PysaurusError, ApplicationError)
    assert issubclass(PysaurusError, (ApplicationError,))
    assert not (issubclass(ApplicationError, (PysaurusError,)))
