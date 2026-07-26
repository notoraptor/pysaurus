"""Rendering property values for display, in the two registers a UI needs.

A `bool` property has no stored enumeration: its domain is implied by the type
and derived by `PropType.possible_values` (see OPEN_DOMAIN_PROP_TYPES). Every
frontend that wants to show or offer those values therefore has to spell them
out itself -- which is exactly the duplication this module removes.

The two registers are deliberately distinct:

- `format_prop_value` is for a value the user *picks*: a bool then reads as the
  answer to a question, "Yes" or "No".
- `format_prop_literal` is for a value that is merely *listed*, in a table or a
  domain: a bool then reads as the literal it is, "true" or "false". A listing
  states what a property holds; it does not ask anything.
"""

from pysaurus.core.language import say
from pysaurus.properties.properties import PropType, PropUnitType


def format_prop_value(prop_type: PropType, value: PropUnitType) -> str:
    """Label for a value the user picks or reads in an editor."""
    if prop_type.type == "bool":
        return say("Yes") if value else say("No")
    return str(value)


def format_prop_literal(prop_type: PropType, value: PropUnitType) -> str:
    """Label for a value that is listed rather than picked."""
    if prop_type.type == "bool":
        return say("true") if value else say("false")
    return str(value)


def format_prop_domain(prop_type: PropType) -> list[str] | None:
    """The values a property accepts, ready to display, or None if unconstrained.

    This is where the implicit domain of a bool surfaces: it carries no
    enumeration row, yet the type still knows it accepts exactly False and
    True, in that order.
    """
    values = prop_type.possible_values
    if values is None:
        return None
    return [format_prop_literal(prop_type, value) for value in values]
