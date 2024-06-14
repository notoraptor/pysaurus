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

Number of characters in Unicode v15.0.0: 149,186
Loaded 2 fonts
43251 / 149186
multiple support: 571
1600
42222

Number of characters in Unicode v15.0.0: 149,186
Loaded 170 fonts
73064 / 149186
multiple support: 48367
1614
44812

Unicode v15.0.0
Number of characters:  149186
Number of blocks: 321
Loaded 160 fonts
...
73051 / 149186
multiple support: 24812
1614
44812

80562 / 149186
multiple support: 24815
1614
44812
-----
110510 / 149186
multiple support: 34437
1614
44812
"""
import json
import os.path
from collections import Counter
from typing import Dict, List

import unicodedataplus
from fontTools.ttLib import TTFont
from fontTools.ttLib.ttCollection import TTCollection

from pysaurus.core.unicode_utils import Unicode
from resource.fonts import (
    FOLDER_FONT,
    NOTO_FONTS,
    PATH_SOURCE_HAN_SANS_JP,
    PATH_SOURCE_SANS_REGULAR,
    get_fonts,
    get_noto_fonts,
    get_noto_sans_fonts,
)

priority = {
    "Basic Latin": ["Noto Sans Regular"],
    "Latin-1 Supplement": ["Noto Sans Regular"],
    "Syriac": ["Noto Sans Syriac Regular"],
    "General Punctuation": ["Noto Sans Regular"],
    "Enclosed Alphanumerics": ["Noto Sans Symbols Regular"],
    "Box Drawing": ["Noto Sans JP"],
    "Block Elements": ["Noto Sans JP"],
    "Geometric Shapes": ["Noto Sans Symbols 2 Regular"],
    "CJK Radicals Supplement": ["Noto Sans JP"],
    "Kangxi Radicals": ["Noto Sans JP"],
    "Ideographic Description Characters": ["Noto Sans JP"],
    "CJK Symbols and Punctuation": ["Noto Sans JP"],
    "Hiragana": ["Noto Sans JP"],
    "Katakana": ["Noto Sans JP"],
    "Bopomofo": ["Noto Sans JP"],
    "Kanbun": ["Noto Sans JP"],
    "CJK Strokes": ["Noto Sans JP"],
    "Katakana Phonetic Extensions": ["Noto Sans JP"],
    "Enclosed CJK Letters and Months": ["Noto Sans JP"],
    "CJK Compatibility": ["Noto Sans JP"],
    "Yijing Hexagram Symbols": ["Noto Sans Symbols 2 Regular"],
    "Common Indic Number Forms": ["Noto Sans Devanagari Regular"],
    "Vertical Forms": ["Noto Sans JP"],
    "CJK Compatibility Forms": ["Noto Sans JP"],
    "Small Form Variants": ["Noto Sans JP"],
    "Coptic Epact Numbers": ["Noto Sans Symbols 2 Regular"],
    "Mayan Numerals": ["Noto Sans Symbols 2 Regular"],
    "Tai Xuan Jing Symbols": ["Noto Sans Symbols 2 Regular"],
    "Counting Rod Numerals": ["Noto Sans Symbols 2 Regular"],
}


class FontUtils:
    def __init__(self, path: str, font_index=-1, allow_vid=NotImplemented):
        self._path = path
        self._font = TTFont(path, fontNumber=font_index, allowVID=allow_vid)

        # (2024/06/11) https://stackoverflow.com/a/72228817
        # fontFamilyName = self._font['name'].getDebugName(1)
        self.name: str = self._font["name"].getDebugName(4)
        self._unicode_map: dict = self._font.getBestCmap()
        # self._unicode_map = self._get_first_unicode_cmap()
        if self._unicode_map is None:
            raise ValueError(f"Cannot find best unicode table in TTF font: {self.name}")

    def _get_first_unicode_cmap(self):
        for cmap in self._font["cmap"].tables:
            if cmap.isUnicode():
                unicode_table = cmap
                break
        else:
            raise ValueError(f"Cannot find unicode table in TTF font: {self.name}")
        print(
            self.name,
            len(unicode_table.cmap),
            unicode_table.platformID,
            unicode_table.platEncID,
        )
        return unicode_table.cmap

    def _get_supported(self, unicode_table):
        """
        2024/06/11
        https://stackoverflow.com/a/43857892
        """
        return [
            (c, unicode_table.cmap[ord(c)])
            for c in Unicode.characters()
            if ord(c) in unicode_table.cmap
        ]

    @property
    def font(self):
        return self._font

    def supported(self):
        return [
            (chr(char_int), char_name)
            for char_int, char_name in self._unicode_map.items()
        ]

    def supports(self, character):
        return self._unicode_map.get(ord(character), None)


def main(path, font_index=-1):
    fu = FontUtils(path, font_index)
    print(len(fu.supported()))


def _percent(a, b):
    return round(a * 100 / b, 2)


def save_noto_fonts():
    output_path = os.path.join(FOLDER_FONT, "noto.json")
    output = get_noto_sans_fonts()
    with open(output_path, "w") as file:
        json.dump(output, file, indent=1)
    print(f"Saved paths for {len(NOTO_FONTS)} Noto fonts at:", output_path)


def check_unicode_coverage(font_table: Dict[str, str]):
    blocks: Dict[str, List[str]] = {}
    for c in Unicode.characters():
        block = unicodedataplus.block(c)
        blocks.setdefault(block, []).append(c)
    nb_characters = sum(len(chars) for chars in blocks.values())
    print(f"Unicode v{Unicode.VERSION}")
    print("Number of characters:", f"{nb_characters: }")
    print("Number of blocks:", len(blocks))

    fonts = []
    for path in font_table.values():
        if path.endswith(".ttc"):
            with TTCollection(path, lazy=True) as coll:
                nb_fonts = len(coll)
            print("TTC", nb_fonts)
            for i in range(nb_fonts):
                fonts.append(FontUtils(path, font_index=i))
        else:
            fonts.append(FontUtils(path))
    print("Loaded", len(fonts), "fonts")

    nb_supported = 0
    nb_multiple_support = 0
    block_coverage = {}
    unsupported_blocks = []
    with open("multi-support.txt", "w", encoding="utf-8") as file:
        for block, chars in blocks.items():
            block_support_count = Counter()
            for c in chars:
                local_supported = [font.name for font in fonts if font.supports(c)]
                block_support_count.update(local_supported)
                nb_supported += bool(local_supported)
                nb_multiple_support += len(local_supported) > 1
                if len(local_supported) > 1:
                    print(f"[{c}]", ", ".join(local_supported), file=file)
            if block_support_count.total():
                block_support = block_support_count.most_common()
                max_support = block_support[0][1]
                most_support = [t for t in block_support if t[1] == max_support]
                block_coverage[block] = most_support
                if len(most_support) > 1:
                    print(f"{block} ({len(chars)})")
                    for name, count in most_support:
                        print(f"\t{name} => {count} : {_percent(count, len(chars))} %")
            else:
                unsupported_blocks.append(block)
    if unsupported_blocks:
        print()
        print("** Unsupported blocks **:")
        for block in unsupported_blocks:
            print(f"\t(x) {block} => {len(blocks[block])}")

    multiple_support = {
        block: {
            "supported": coverage[0][1],
            "block": len(blocks[block]),
            "percent": _percent(coverage[0][1], len(blocks[block])),
            "fonts": [couple[0] for couple in coverage],
        }
        for block, coverage in block_coverage.items()
        if len(coverage) > 1
    }
    with open("multiple_support.json", "w") as file:
        json.dump(multiple_support, file, indent=1)

    print(nb_supported, "/", nb_characters)
    print("multiple support:", nb_multiple_support)


if __name__ == "__main__":
    _r = get_noto_fonts
    _paths = (PATH_SOURCE_SANS_REGULAR, PATH_SOURCE_HAN_SANS_JP)
    check_unicode_coverage(get_fonts())
    main(PATH_SOURCE_SANS_REGULAR)
    main(PATH_SOURCE_HAN_SANS_JP)
    # save_noto_fonts()
