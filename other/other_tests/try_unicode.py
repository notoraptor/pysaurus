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
from collections import Counter
from typing import Dict, List

import unicodedataplus
from fontTools.ttLib.ttCollection import TTCollection

from pysaurus.core.unicode_utils import Unicode
from resource.fonts import PATH_SOURCE_HAN_SANS_JP, PATH_SOURCE_SANS_REGULAR, get_fonts
from resource.fonts.font_utils import FontUtils


def main(path, font_index=-1):
    fu = FontUtils(path, font_index)
    print(len(fu.supported()))


def _percent(a, b):
    return round(a * 100 / b, 2)


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
    _paths = (PATH_SOURCE_SANS_REGULAR, PATH_SOURCE_HAN_SANS_JP)
    check_unicode_coverage(get_fonts())
    main(PATH_SOURCE_SANS_REGULAR)
    main(PATH_SOURCE_HAN_SANS_JP)
    # save_noto_fonts()
