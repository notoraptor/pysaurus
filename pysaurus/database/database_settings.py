from dataclasses import dataclass


@dataclass(slots=True)
class DatabaseSettings:
    """Per-database settings, stored in the collection row."""

    # Plain string property that "Generalize title" targets without asking.
    generalize_title_property: str | None = None


def can_hold_generalized_titles(prop_type) -> bool:
    """A non-enumerated string property: what "Generalize title" writes into."""
    return prop_type.type == "str" and not prop_type.enumeration
