from pysaurus.database.semantic_text import (
    SemanticText,
    separate_characters_and_numbers,
)


def test_simple_semantic():
    assert SemanticText("abc") < SemanticText("abd")
    assert "a2" > "a10"
    assert SemanticText("a2") < SemanticText("a10")


def test_semantic_text():
    print()
    texts = (
        "my.anime.s01.e6",
        "my.anime.s01.e05",
        "my.anime.s01.e20",
        "my.anime.s01.e17",
        "my.anime.s01.e11",
        "my_anime.s02.e4",
        "my_anime.s02.e40",
        "my_anime.s02.e3",
        "maanime124",
        r"H:\donnees\torrents\anime\vostfr\[Tsundere-Raws] "
        r"Shin Ikki Tousen - 03 VOSTFR (CR) [WEB 1080p x264 AAC].mkv",
        r"H:\donnees\torrents\anime\vostfr\[Elecman] Ikki Tousen Integral S1-S7 [BDRIP "
        r"CUSTOM][1080p x265 10bits Multi,Vostfr]\[Elecman] Ikki Tousen S2 Dragon "
        r"Destiny [BDRIP CUSTOM][1080p x265 10bits Multi]V2\[Elecman] Ikki Tousen "
        r"Dragon Destiny E01 [BDRIP CUSTOM][1080p x265 10bits Multi].mkv",
        r"H:\donnees\torrents\anime\vostfr\[Elecman] Ikki Tousen Integral S1-S7 [BDRIP "
        r"CUSTOM][1080p x265 10bits Multi,Vostfr]\[Elecman] Ikki Tousen S1 [BDRIP "
        r"CUSTOM][1080p x265 10bits Multi]V2\[Elecman] Ikki Tousen E13 [BDRIP "
        r"CUSTOM][1080p x265 10bits Multi].mkv",
    )
    semantics = [SemanticText(text) for text in texts]
    assert list(v.value for v in sorted(semantics)) == [
        r"H:\donnees\torrents\anime\vostfr\[Elecman] Ikki Tousen Integral S1-S7 [BDRIP "
        r"CUSTOM][1080p x265 10bits Multi,Vostfr]\[Elecman] Ikki Tousen S1 [BDRIP "
        r"CUSTOM][1080p x265 10bits Multi]V2\[Elecman] Ikki Tousen E13 [BDRIP "
        r"CUSTOM][1080p x265 10bits Multi].mkv",
        r"H:\donnees\torrents\anime\vostfr\[Elecman] Ikki Tousen Integral S1-S7 [BDRIP "
        r"CUSTOM][1080p x265 10bits Multi,Vostfr]\[Elecman] Ikki Tousen S2 Dragon "
        r"Destiny [BDRIP CUSTOM][1080p x265 10bits Multi]V2\[Elecman] Ikki Tousen "
        r"Dragon Destiny E01 [BDRIP CUSTOM][1080p x265 10bits Multi].mkv",
        r"H:\donnees\torrents\anime\vostfr\[Tsundere-Raws] "
        r"Shin Ikki Tousen - 03 VOSTFR (CR) [WEB 1080p x264 AAC].mkv",
        "maanime124",
        "my.anime.s01.e05",
        "my.anime.s01.e6",
        "my.anime.s01.e11",
        "my.anime.s01.e17",
        "my.anime.s01.e20",
        "my_anime.s02.e3",
        "my_anime.s02.e4",
        "my_anime.s02.e40",
    ]


def test_consume():
    assert list(
        separate_characters_and_numbers(
            "My age is 020.444 and⁸⁵³34³³₅ab₅₄₅10₄ my name is Eminem10"
        )
    ) == [
        "M",
        "y",
        " ",
        "a",
        "g",
        "e",
        " ",
        "i",
        "s",
        " ",
        20,
        ".",
        444,
        " ",
        "a",
        "n",
        "d",
        853,
        34,
        33,
        5,
        "a",
        "b",
        545,
        10,
        4,
        " ",
        "m",
        "y",
        " ",
        "n",
        "a",
        "m",
        "e",
        " ",
        "i",
        "s",
        " ",
        "E",
        "m",
        "i",
        "n",
        "e",
        "m",
        10,
    ]
