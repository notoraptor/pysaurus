import logging

from pysaurus.core.dict_file_format import dff_dump
from pysaurus.core.language import (
    DEFAULT_LANGUAGE,
    available_languages,
    canonical_language,
    get_language,
    key_of,
    say,
    set_language,
)


def _install_french(tmp_path, translations: dict[str, str]):
    """Write en.txt + fr.txt catalogs mapping given English texts."""
    english = {key_of(text): text for text in translations}
    french = {key_of(text): translated for text, translated in translations.items()}
    dff_dump(english, tmp_path / "en.txt")
    dff_dump(french, tmp_path / "fr.txt")


def test_say_passthrough_by_default():
    assert get_language() == DEFAULT_LANGUAGE
    assert say("Hello world") == "Hello world"
    assert say("Error {name}: {message}", name="A", message="B") == "Error A: B"


def test_set_language_loads_translations(tmp_path):
    _install_french(tmp_path, {"Move": "Déplacement"})
    set_language("fr", tmp_path)
    assert get_language() == "fr"
    assert say("Move") == "Déplacement"


def test_missing_key_falls_back_to_source(tmp_path):
    _install_french(tmp_path, {"Move": "Déplacement"})
    set_language("fr", tmp_path)
    assert say("Unknown text") == "Unknown text"
    assert say("Done {count}", count=3) == "Done 3"


def test_placeholders_in_translation(tmp_path):
    _install_french(tmp_path, {"Error {name}: {message}": "Erreur {name} : {message}"})
    set_language("fr", tmp_path)
    assert say("Error {name}: {message}", name="X", message="boom") == "Erreur X : boom"


def test_bad_translation_falls_back_to_source(tmp_path, caplog):
    _install_french(tmp_path, {"Error {name}": "Erreur {nom}"})
    set_language("fr", tmp_path)
    with caplog.at_level(logging.WARNING, logger="pysaurus.core.language"):
        assert say("Error {name}", name="X") == "Error X"
    assert any("bad placeholders" in message for message in caplog.messages)


def test_bad_translation_any_exception_falls_back(tmp_path, caplog):
    """TypeError ({x[0]} on an int) and AttributeError ({x.y}) also fall back."""
    _install_french(
        tmp_path, {"Done {count}": "Fini {count[0]}", "Hi {name}": "Salut {name.x}"}
    )
    set_language("fr", tmp_path)
    with caplog.at_level(logging.WARNING, logger="pysaurus.core.language"):
        assert say("Done {count}", count=5) == "Done 5"
        assert say("Hi {name}", name="Bob") == "Hi Bob"
    assert len([m for m in caplog.messages if "bad placeholders" in m]) == 2


def test_unknown_language_yields_passthrough(tmp_path):
    set_language("klingon", tmp_path)
    assert get_language() == "klingon"
    assert say("Hello") == "Hello"


def test_back_to_english_resets_catalog(tmp_path):
    _install_french(tmp_path, {"Move": "Déplacement"})
    set_language("fr", tmp_path)
    assert say("Move") == "Déplacement"
    set_language(DEFAULT_LANGUAGE)
    assert say("Move") == "Move"


def test_available_languages(tmp_path):
    _install_french(tmp_path, {"Move": "Déplacement"})
    dff_dump({"Key_1": "vieux texte"}, tmp_path / "fr.obsolete.txt")
    assert available_languages(tmp_path) == ["en", "fr"]


def test_available_languages_missing_folder(tmp_path):
    assert available_languages(tmp_path / "nope") == ["en"]


def test_canonical_language():
    assert canonical_language("english") == "en"
    assert canonical_language("français") == "fr"
    assert canonical_language("fr") == "fr"  # already a code
    assert canonical_language("klingon") == "klingon"  # unknown: unchanged


def test_key_of_is_stable_and_readable():
    key = key_of("Collect videos")
    assert key == key_of("Collect videos")
    assert key.startswith("CollectVideos_")
    assert key != key_of("Collect video")


def test_multiline_text(tmp_path):
    text = "First line.\n\nSecond line."
    _install_french(tmp_path, {text: "Première ligne.\n\nSeconde ligne."})
    set_language("fr", tmp_path)
    assert say(text) == "Première ligne.\n\nSeconde ligne."
