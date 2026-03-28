from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.functions import string_to_pieces
from pysaurus.core.semantic_text import pad_numbers_in_string


def pysaurus_get_extension(filename: str) -> str:
    return AbsolutePath(filename).extension


def pysaurus_get_file_title(filename: str) -> str:
    return AbsolutePath(filename).file_title


def pysaurus_get_title(filename: str, meta_title: str) -> str:
    return meta_title or AbsolutePath(filename).file_title


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


def pysaurus_text_with_numbers(text: str, padding: int) -> str:
    return pad_numbers_in_string(text, padding)
