import os
from multiprocessing import Manager, Pool

from saurus.language import Language


def test_lang():
    lang = Language()
    text = "Hello, world! How are you?"
    translation = lang(text)
    footprint = lang.key_of(text)
    assert translation == text
    lang.set_language("french")
    assert lang(text) == translation
    assert lang.key_of(text) == footprint
    assert (
        lang("hello {world}, it's {person}", world="terre", person="me")
        == "hello terre, it's me"
    )


def test_lang_folder():
    lang = Language(folder=os.path.dirname(__file__))
    text_1 = "Hello, world! How are you?"
    footprint = lang.key_of(text_1)
    assert lang(text_1) == text_1
    lang.set_language("french")
    assert lang(text_1) == "Bonjour, monde! Comment vas-tu?"
    assert lang.key_of(text_1) == footprint
    lang.set_language(lang.default)
    text_2 = "a b c d e f g h i j k l m n o p q r s t u v w z y z"
    assert lang(text_2) == text_2
    lang.set_language("french")
    assert lang(text_2) == "les lettres de l'alphabet en minuscule"


def _check_lang(lang: Language, i: int):
    lang(f"Hello {i}")


def test_language_accumulation():
    lang = Language()
    assert len(lang) == 0
    jobs = [(lang, i) for i in range(10)]
    for job in jobs:
        _check_lang(*job)
    assert len(lang) == 10


def test_language_with_multiprocess():
    with Manager() as manager:
        d = manager.dict()
        lang = Language(dictionary=d)
        assert len(lang) == 0
        jobs = [(lang, i) for i in range(10)]
        with Pool(os.cpu_count()) as p:
            p.starmap(_check_lang, jobs)
        assert len(lang) == 10
