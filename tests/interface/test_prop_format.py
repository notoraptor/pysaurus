"""The two display registers for property values, and the implicit bool domain.

A value the user *picks* reads as an answer ("Yes"/"No"); a value merely
*listed* reads as the literal it is ("true"/"false"). say() falls back to the
English source when no catalog is loaded, so most of these assert the English
text, plus one round-trip through the real French catalog.
"""

import pytest

from pysaurus.core.language import set_language
from pysaurus.interface.common.prop_format import (
    format_prop_domain,
    format_prop_literal,
    format_prop_value,
)
from pysaurus.properties.properties import PropType


@pytest.fixture
def bool_prop() -> PropType:
    return PropType.define("watched", "bool", False, False)


class TestRegisters:
    @pytest.mark.parametrize(
        "value,picked,listed", [(True, "Yes", "true"), (False, "No", "false")]
    )
    def test_bool_reads_differently_picked_and_listed(
        self, bool_prop, value, picked, listed
    ):
        assert format_prop_value(bool_prop, value) == picked
        assert format_prop_literal(bool_prop, value) == listed

    def test_other_types_read_the_same_in_both_registers(self):
        prop = PropType.define("rating", "int", 0, False)
        assert format_prop_value(prop, 3) == "3"
        assert format_prop_literal(prop, 3) == "3"


class TestDomain:
    def test_bool_domain_is_implicit_but_displayable(self, bool_prop):
        """Nothing is stored, yet the domain is known -- that is the point."""
        assert bool_prop.enumeration is None
        assert format_prop_domain(bool_prop) == ["false", "true"]

    def test_enumerated_property_shows_its_values(self):
        prop = PropType.define("rating", "int", [1, 2, 3], False)
        assert format_prop_domain(prop) == ["1", "2", "3"]

    def test_free_property_has_no_domain(self):
        assert format_prop_domain(PropType.define("tag", "str", "", True)) is None


def test_both_registers_are_translated(bool_prop):
    """End to end through the packaged French catalog."""
    set_language("fr")
    assert format_prop_domain(bool_prop) == ["faux", "vrai"]
    assert format_prop_value(bool_prop, True) == "Oui"
    assert format_prop_value(bool_prop, False) == "Non"
