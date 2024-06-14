import sys

from unicodedata import category, unidata_version


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
