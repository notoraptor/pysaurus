"""Static extraction of translatable strings (lupdate-style).

Scans the ``pysaurus`` package for ``say("English literal", ...)`` calls and
regenerates the language catalogs in ``pysaurus/languages/``:

- ``english.txt`` is fully regenerated from the source code (reference).
- Every other ``<language>.txt`` is merged: existing translations are kept,
  missing keys are added with the English text as value (i.e. "to translate"),
  and keys no longer in the source are moved to ``<language>.obsolete.txt``
  so translations are never silently lost.
- Translated entries must keep the same ``{placeholders}`` as the source.
- Catalog files are only rewritten when their content actually changes.

Violations (the script fails on any of them):

- the first argument of ``say(...)`` is not a string literal (f-string,
  variable, call...);
- the literal ends with whitespace or a newline (the dff format strips it on
  load, so such a text could never match its translation at runtime);
- ``say`` is imported under an alias, or called as ``language.say(...)`` —
  the extractor only recognizes direct ``say("...")`` calls.

Usage:
    uv run poe i18n
    uv run -m pysaurus.scripts.extract_language
"""

import ast
import string
import sys
from dataclasses import dataclass
from pathlib import Path

from pysaurus import package_dir
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.dict_file_format import dff_dumps, dff_load
from pysaurus.core.language import (
    DEFAULT_LANGUAGE,
    LANGUAGE_EXTENSION,
    OBSOLETE_SUFFIX,
    available_languages,
    key_of,
    languages_folder,
)

SAY_MODULE = "pysaurus.core.language"


@dataclass(slots=True)
class Violation:
    path: str
    lineno: int
    reason: str

    def __str__(self):
        return f"{self.path}:{self.lineno}: {self.reason}"


def _print_status(ok: bool, detail: str = "") -> None:
    """Print a final green OK / red FAILED status line."""
    stream = sys.stdout if ok else sys.stderr
    message = ("i18n: OK" if ok else "i18n: FAILED") + (
        f" ({detail})" if detail else ""
    )
    if stream.isatty():
        color = "\x1b[92m" if ok else "\x1b[91m"
        message = f"{color}{message}\x1b[0m"
    print(message, file=stream)


def extract_texts(
    source: str, path: str = "<source>"
) -> tuple[dict[str, str], list[Violation]]:
    """Extract English texts from say(...) calls in a Python source.

    :return: ({derived_key: text}, violations)
    """
    texts: dict[str, str] = {}
    violations: list[Violation] = []
    for node in ast.walk(ast.parse(source, filename=path)):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if node.module == SAY_MODULE and alias.name == "say" and alias.asname:
                    violations.append(
                        Violation(
                            path,
                            node.lineno,
                            f"say must not be imported under an alias"
                            f" ({alias.asname}): the extractor would skip its calls",
                        )
                    )
            continue
        if not isinstance(node, ast.Call):
            continue
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "say"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "language"
        ):
            violations.append(
                Violation(
                    path,
                    node.lineno,
                    "call say directly (from pysaurus.core.language import say):"
                    " the extractor does not recognize language.say(...)",
                )
            )
            continue
        if not (isinstance(node.func, ast.Name) and node.func.id == "say"):
            continue
        if not node.args:
            violations.append(
                Violation(path, node.lineno, "say() without positional argument")
            )
            continue
        first = node.args[0]
        if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
            violations.append(
                Violation(
                    path,
                    first.lineno,
                    "first argument of say() must be a string literal",
                )
            )
        elif first.value != first.value.rstrip():
            violations.append(
                Violation(
                    path,
                    first.lineno,
                    "say() literal must not end with whitespace"
                    " (the dff format strips it on load)",
                )
            )
        else:
            texts[key_of(first.value)] = first.value
    return texts, violations


def merge_catalog(
    english: dict[str, str], existing: dict[str, str]
) -> tuple[dict[str, str], dict[str, str]]:
    """Merge a translation catalog against the English reference.

    :return: (merged, orphans). Merged has exactly the English keys: existing
        translations kept, missing ones filled with the English text. Orphans
        are entries whose key no longer exists in the reference.
    """
    merged = {key: existing.get(key, text) for key, text in english.items()}
    orphans = {key: value for key, value in existing.items() if key not in english}
    return merged, orphans


def _placeholders(text: str) -> set[str]:
    # Full field expressions on purpose: {name}, {name[0]} and {name.x} are
    # all different, and a translation must use exactly the source's fields.
    return {
        field for _, field, _, _ in string.Formatter().parse(text) if field is not None
    }


def validate_placeholders(
    english: dict[str, str], merged: dict[str, str], language: str
) -> list[str]:
    """Check that translated entries keep the same {placeholders} as the source."""
    errors = []
    for key, translation in merged.items():
        source = english[key]
        if translation == source:
            continue  # untranslated entry
        try:
            expected = _placeholders(source)
        except ValueError:
            continue  # source braces are not format fields, nothing to compare
        try:
            found = _placeholders(translation)
        except ValueError:
            errors.append(f"[{language}] {key}: malformed braces in translation")
            continue
        if expected != found:
            errors.append(
                f"[{language}] {key}: placeholders differ"
                f" (source: {sorted(expected)}, translation: {sorted(found)})"
            )
    return errors


def _write_if_changed(dictionary: dict[str, str], path: AbsolutePath) -> None:
    data = dff_dumps(dictionary).encode("utf-8")
    if path.isfile() and path.read_binary_file() == data:
        return
    with open(path.path, "wb") as file:
        file.write(data)


def run(source_dir: str | None = None, languages_dir: str | None = None) -> int:
    source_dir = source_dir or package_dir()
    folder = languages_folder(languages_dir)

    english: dict[str, str] = {}
    violations: list[Violation] = []
    for py_path in sorted(Path(source_dir).rglob("*.py")):
        texts, file_violations = extract_texts(
            py_path.read_text(encoding="utf-8"), str(py_path)
        )
        english.update(texts)
        violations.extend(file_violations)
    if violations:
        for violation in violations:
            print(violation, file=sys.stderr)
        _print_status(False, f"{len(violations)} violation(s)")
        return 1

    english = dict(sorted(english.items()))

    # Compute every merge and validate placeholders BEFORE touching the disk,
    # so a failed run (bad placeholders) leaves the catalogs exactly as they
    # were instead of writing a half-updated set of files.
    writes: list[tuple[dict[str, str], AbsolutePath]] = [
        (english, AbsolutePath.join(folder, DEFAULT_LANGUAGE + LANGUAGE_EXTENSION))
    ]
    summaries: list[str] = [f"{DEFAULT_LANGUAGE}: {len(english)} entries"]
    errors: list[str] = []
    for language in available_languages(folder):
        if language == DEFAULT_LANGUAGE:
            continue
        lang_path = AbsolutePath.join(folder, language + LANGUAGE_EXTENSION)
        merged, orphans = merge_catalog(english, dff_load(lang_path))
        errors.extend(validate_placeholders(english, merged, language))
        writes.append((dict(sorted(merged.items())), lang_path))
        if orphans:
            obsolete_path = AbsolutePath.join(folder, language + OBSOLETE_SUFFIX)
            obsolete = dff_load(obsolete_path) if obsolete_path.isfile() else {}
            obsolete.update(orphans)
            writes.append((dict(sorted(obsolete.items())), obsolete_path))
        untranslated = sum(1 for key, value in merged.items() if value == english[key])
        summaries.append(
            f"{language}: {len(merged)} entries, {untranslated} untranslated,"
            f" {len(orphans)} moved to obsolete"
        )

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        _print_status(False, f"{len(errors)} placeholder error(s)")
        return 1

    folder.mkdir()
    for dictionary, path in writes:
        _write_if_changed(dictionary, path)
    for summary in summaries:
        print(summary)
    _print_status(True)
    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
