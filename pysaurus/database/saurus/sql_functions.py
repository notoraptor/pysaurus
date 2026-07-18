from pysaurus.core.functions import string_to_pieces
from pysaurus.core.semantic_text import encode_numbers_for_sort


def pysaurus_text_to_fts(text: str) -> str | None:
    """Convert text to FTS5-friendly format with camelCase splitting.

    Registered as a SQL function for use in triggers and queries.
    Returns NULL for NULL input.
    """
    if text is None:
        return None
    pieces = string_to_pieces(text)
    pieces_low = string_to_pieces(text.lower())
    if pieces != pieces_low:
        pieces = pieces + pieces_low
    return " ".join(pieces)


def pysaurus_text_with_numbers(text: str) -> str:
    return encode_numbers_for_sort(text)
