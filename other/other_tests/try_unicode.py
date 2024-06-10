"""
2024/06/09
https://stackoverflow.com/a/68992289
"""

import sys

from unicodedata import category, unidata_version

chars = []
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
    chars.append(c)

print(f"Number of characters in Unicode v{unidata_version}: {len(chars):,}")

sentence = " ".join(chars)
with open(f"unicode_v{unidata_version}.html", mode="w", encoding="utf-8") as file:
    file.write(f"<html><body><p>{sentence}</p></body></html>")
