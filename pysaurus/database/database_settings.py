from dataclasses import dataclass


@dataclass(slots=True)
class DatabaseSettings:
    """Per-database settings, stored in the collection row."""

    # Plain string property that "Generalize title" targets without asking.
    generalize_title_property: str | None = None
    # "Copy similarity infos": overwrite a unique property valued differently
    # on the destination, instead of keeping the destination's value.
    copy_overwrites_unique_properties: bool = False


def can_hold_generalized_titles(prop_type) -> bool:
    """A non-enumerated string property: what "Generalize title" writes into."""
    return prop_type.type == "str" and not prop_type.enumeration


def can_accumulate_titles(prop_type) -> bool:
    """A multiple one: where "Copy similarity infos" stacks a video's titles."""
    return can_hold_generalized_titles(prop_type) and prop_type.multiple
