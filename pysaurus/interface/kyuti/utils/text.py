from pysaurus.core.language import say
from pysaurus.database.saved_search import SavedSearch

LABEL_MAX_LENGTH = 60


def elide(label: str, max_length: int = LABEL_MAX_LENGTH) -> str:
    """Cut a label for menus and combos, with a trailing ellipsis."""
    if len(label) <= max_length:
        return label
    return label[: max_length - 3] + "..."


def saved_search_tooltip(search: SavedSearch) -> str:
    """The whole entry, name included, for a label that may be cut."""
    if search.name:
        return say(
            "{name}: {expression}", name=search.name, expression=search.expression
        )
    return search.expression
