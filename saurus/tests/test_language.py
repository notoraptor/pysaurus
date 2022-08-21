import os

from saurus.language import Language, say


def test_say():
    text = "Hello, world! How are you?"
    translation = say(text)
    footprint = say.keyof(text)
    assert translation == text
    say.set_language("french")
    assert say(text) == translation
    assert say.keyof(text) == footprint


def test_say_folder():
    s = Language()
    s.set_folder(os.path.dirname(__file__))
    text = "Hello, world! How are you?"
    translation = s(text)
    footprint = s.keyof(text)
    assert translation == text
    s.set_language("french")
    assert s(text) == "Bonjour, monde! Comment vas-tu?"
    assert s.keyof(text) == footprint
    long_text = "a b c d e f g h i j k l m n o p q r s t u v w z y z"
    s.set_language(s.default)
    assert s(long_text) == long_text
    s.set_language("french")
    assert s(long_text) == "les lettres de l'alphabet en minuscule"
