"""Translation system for user-facing strings (i18n).

"i18n" abbreviates "internationalization" — a numeronym: initial "i", 18
letters, final "n" (same family as "l10n" for "localization"). The term names
this system across the project: this module, the ``poe i18n`` task and the
extraction script (``pysaurus/scripts/extract_language.py``).

``say("English literal", **placeholders)`` translates a string, using the
English source text itself as the key (like Qt's ``tr()`` or gettext).

The catalog is loaded once at startup (``Application.__init__`` calls
``set_language`` before any thread is spawned) and is read-only afterwards:
looking up an unknown string just returns the English source text.

Language files live in ``pysaurus/languages/`` (dff format, one file per
language, keyed by ``key_of`` derived keys). They are maintained offline by
the static extraction script (``uv run poe i18n``), never written at runtime.
"""

import logging

from pysaurus import package_dir
from pysaurus.core import dict_file_format as dff
from pysaurus.core.absolute_path import AbsolutePath, PathType
from pysaurus.core.functions import string_to_pieces
from pysaurus.core.modules import FNV64

logger = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "english"
LANGUAGE_EXTENSION = ".txt"
OBSOLETE_SUFFIX = ".obsolete.txt"

_current_language: str = DEFAULT_LANGUAGE
# Maps English source text to translated text, for the current language.
_catalog: dict[str, str] = {}


def say(text: str, **placeholders) -> str:
    """Translate an English source text, formatting placeholders if given."""
    translation = _catalog.get(text, text)
    if not placeholders:
        return translation
    if translation is not text:
        try:
            return translation.format(**placeholders)
        except Exception:
            # Whatever way the translation data is malformed (KeyError,
            # TypeError on {x[0]}, AttributeError on {x.y}, ...), fall back
            # to the English source rather than crashing the caller.
            logger.warning(
                f"[{_current_language}] bad placeholders in translation of: {text}"
            )
    return text.format(**placeholders)


def key_of(text: str) -> str:
    """Derive the (single-line) catalog key of an English source text."""
    pieces = string_to_pieces(text)
    if len(pieces) > 20:
        pieces = pieces[:20] + ["..."]
    hl_key = "".join(piece.title() for piece in pieces)
    return f"{hl_key}_{FNV64.hash(text)}"


def set_language(name: str, folder: PathType | None = None) -> None:
    """Load the catalog for a language, replacing the current one.

    Missing files just yield an empty catalog (``say`` then falls back to
    English source texts).
    """
    global _current_language, _catalog
    catalog: dict[str, str] = {}
    if name != DEFAULT_LANGUAGE:
        base = languages_folder(folder)
        english_path = AbsolutePath.join(base, DEFAULT_LANGUAGE + LANGUAGE_EXTENSION)
        target_path = AbsolutePath.join(base, name + LANGUAGE_EXTENSION)
        if english_path.isfile() and target_path.isfile():
            english = dff.dff_load(english_path)
            target = dff.dff_load(target_path)
            catalog = {
                english[key]: value for key, value in target.items() if key in english
            }
        else:
            logger.warning(f"No language file found for: {name}")
    _current_language = name
    _catalog = catalog


def get_language() -> str:
    return _current_language


def available_languages(folder: PathType | None = None) -> list[str]:
    """List installed languages (English is always available)."""
    names = {DEFAULT_LANGUAGE}
    base = languages_folder(folder)
    if base.isdir():
        for entry in base.listdir():
            if entry.endswith(LANGUAGE_EXTENSION) and not entry.endswith(
                OBSOLETE_SUFFIX
            ):
                names.add(entry[: -len(LANGUAGE_EXTENSION)])
    return sorted(names)


def languages_folder(folder: PathType | None = None) -> AbsolutePath:
    """Resolve the catalogs folder (default: ``pysaurus/languages/``).

    Single source of truth, shared with the extraction script.
    """
    if folder is None:
        return AbsolutePath.join(package_dir(), "languages")
    return AbsolutePath.ensure(folder)
