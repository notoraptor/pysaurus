import os

from saurus.language import say


def test_say():
    text = "Hello, world! How are you?"
    translation = say(text)
    footprint = say[text]
    assert translation == text
    say.set_language("french")
    assert say(text) == translation
    assert say[text] == footprint


def test_say_folder():
    s = say.new()
    s.set_folder(os.path.dirname(__file__))
    text = "Hello, world! How are you?"
    translation = s(text)
    footprint = s[text]
    assert translation == text
    s.set_language("french")
    assert s(text) == "Bonjour, monde! Comment vas-tu?"
    assert s[text] == footprint
