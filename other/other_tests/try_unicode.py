"""
2024/06/10:
https://www.fileformat.info/info/unicode/category/index.htm
Code 	Description
[Cc] 	Other, Control
[Cf] 	Other, Format
[Cn] 	Other, Not Assigned (no characters in the file have this property)
[Co] 	Other, Private Use
[Cs] 	Other, Surrogate
[LC] 	Letter, Cased
[Ll] 	Letter, Lowercase
[Lm] 	Letter, Modifier
[Lo] 	Letter, Other
[Lt] 	Letter, Titlecase
[Lu] 	Letter, Uppercase
[Mc] 	Mark, Spacing Combining
[Me] 	Mark, Enclosing
[Mn] 	Mark, Nonspacing
[Nd] 	Number, Decimal Digit
[Nl] 	Number, Letter
[No] 	Number, Other
[Pc] 	Punctuation, Connector
[Pd] 	Punctuation, Dash
[Pe] 	Punctuation, Close
[Pf] 	Punctuation, Final quote (may behave like Ps or Pe depending on usage)
[Pi] 	Punctuation, Initial quote (may behave like Ps or Pe depending on usage)
[Po] 	Punctuation, Other
[Ps] 	Punctuation, Open
[Sc] 	Symbol, Currency
[Sk] 	Symbol, Modifier
[Sm] 	Symbol, Math
[So] 	Symbol, Other
[Zl] 	Separator, Line
[Zp] 	Separator, Paragraph
[Zs] 	Separator, Space
"""

import sys

from fontTools.ttLib import TTFont
from unicodedata import category, unidata_version

from resource.fonts import PATH_SOURCE_HAN_SANS_JP, PATH_SOURCE_HAN_SANS_TTC, \
    PATH_SOURCE_SANS_REGULAR


class Unicode:
    VERSION = unidata_version

    @classmethod
    def characters(cls):
        """
        2024/06/09
        https://stackoverflow.com/a/68992289
        """
        for i in range(sys.maxunicode + 1):
            c = chr(i)
            cat = category(c)
            if cat == "Cc":  # control characters
                continue
            if cat == "Co":  # private use
                continue
            if cat == "Cs":  # surrogates
                continue
            if cat == "Cn":  # non-character or reserved
                continue
            yield c


class FontUtils:
    def __init__(self, path: str, font_index=-1):
        self._path = path
        self._font = TTFont(path, fontNumber=font_index)

    def supported(self):
        """
        2024/06/11
        https://stackoverflow.com/a/43857892
        """
        for cmap in self._font["cmap"].tables:
            if cmap.isUnicode():
                unicode_table = cmap
                break
        else:
            raise ValueError(f"Cannot find unicode table in TTF font: {self._path}")
        return [
            (c, unicode_table.cmap[ord(c)])
            for c in Unicode.characters()
            if ord(c) in unicode_table.cmap
        ]


def info():
    chars = list(Unicode.characters())
    print(f"Number of characters in Unicode v{Unicode.VERSION}: {len(chars):,}")


def main(path, font_index=-1):
    print(len(FontUtils(path, font_index).supported()))


if __name__ == "__main__":
    info()
    main(PATH_SOURCE_SANS_REGULAR)
    main(PATH_SOURCE_HAN_SANS_JP)
    main(PATH_SOURCE_HAN_SANS_TTC, 0)
    main(PATH_SOURCE_HAN_SANS_TTC, 1)
    main(PATH_SOURCE_HAN_SANS_TTC, 2)
    main(PATH_SOURCE_HAN_SANS_TTC, 3)
    main(PATH_SOURCE_HAN_SANS_TTC, 4)
