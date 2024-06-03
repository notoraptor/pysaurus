import pytest

from other.supertk import padding


def test_padding():
    assert padding() == (0, 0, 0, 0)
    assert padding(12) == (12, 12, 12, 12)
    assert padding(12, 7) == (12, 7, 12, 7)
    with pytest.raises(AssertionError, match="Ambiguous padding"):
        padding(12, 7, 9)
    assert padding(12, 7, 9, 11) == (12, 7, 9, 11)
