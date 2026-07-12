"""Generate the language-names reference table from Qt's embedded CLDR data.

The ISO 639 / BCP 47 standards define the language *codes*; the IANA registry
only carries English names. The authoritative source for endonyms ("each
language named in its own language") is Unicode CLDR, which Qt embeds — so we
generate the table from `QLocale` rather than downloading anything.

Output: `pysaurus/languages/language_names.json`, mapping each ISO 639-1 code to
its native name (endonym, for display) and English name:

    {"fr": {"native": "français", "english": "French"}, ...}

This is the ONLY place that touches PySide6 in the language stack; the runtime
(`pysaurus/core/language.py`) just reads the generated JSON, so `core` keeps no
PySide6 dependency. Re-run after a Qt/CLDR upgrade:

    uv run -m pysaurus.scripts.generate_language_names
"""

import json
import os

from PySide6.QtCore import QLocale

from pysaurus.core.language import languages_folder

# CLDR returns a region-qualified endonym for a few languages whose default
# locale carries a region ("en" -> "American English"). Override with the plain
# language endonym. Keep this list minimal and only for CLEARLY region-qualified
# names — most multiword endonyms (e.g. "norsk bokmål") are legitimate.
NATIVE_NAME_OVERRIDES = {"en": "English", "es": "español"}


def collect() -> dict[str, dict[str, str]]:
    table: dict[str, dict[str, str]] = {}
    for locale in QLocale.matchingLocales(
        QLocale.Language.AnyLanguage,
        QLocale.Script.AnyScript,
        QLocale.Country.AnyCountry,
    ):
        language = locale.language()
        if language == QLocale.Language.C:
            continue
        code = QLocale.languageToCode(language, QLocale.LanguageCodeType.ISO639Part1)
        if not code or code in table:
            continue
        english = QLocale.languageToString(language)
        native = NATIVE_NAME_OVERRIDES.get(code) or locale.nativeLanguageName()
        table[code] = {
            "native": native or english,  # fall back to English if CLDR is empty
            "english": english,
        }
    return dict(sorted(table.items()))


def main() -> None:
    table = collect()
    path = os.path.join(languages_folder().path, "language_names.json")
    with open(path, "w", encoding="utf-8") as file:
        json.dump(table, file, ensure_ascii=False, indent=2, sort_keys=True)
        file.write("\n")
    print(f"{len(table)} languages written to {path}")


if __name__ == "__main__":
    main()
