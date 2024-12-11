import unicodedata

UNICODE_MATH_CATEGORY = "Sm"
UNICODE_MODIFIED_CATEGORY = "Sk"


def is_word(c: str) -> bool:
    return c.isalnum() or c == "_"


def is_punc(c: str) -> bool:
    uc = unicodedata.category(c)
    return uc.startswith("P") or uc in (
        UNICODE_MATH_CATEGORY,
        UNICODE_MODIFIED_CATEGORY,
    )


def is_currency(c: str) -> bool:
    uc = unicodedata.category(c)
    return uc == "Sc"


CAT_NONE = -1
CAT_SPACE = 0
CAT_WORD = 1
CAT_PUNC = 2
CAT_CURR = 3
CAT_OTHER = 4


def get_category(c: str) -> int:
    if c == " ":
        return CAT_SPACE
    elif is_word(c):
        return CAT_WORD
    elif is_punc(c):
        return CAT_PUNC
    elif is_currency(c):
        return CAT_CURR
    else:
        return CAT_OTHER


def get_previous_word_position(text: str, start: int):
    start = min(max(0, start), len(text) - 1)
    cat = CAT_NONE
    for i in range(start, -1, -1):
        local_cat = get_category(text[i])
        if cat == CAT_NONE:
            if local_cat != CAT_SPACE:
                cat = local_cat
        elif local_cat != cat:
            return i + 1
    else:
        return 0


def get_next_word_position(text: str, start: int):
    start = min(max(0, start), len(text) - 1)
    cat = CAT_NONE
    for i in range(start, len(text)):
        local_cat = get_category(text[i])
        if cat == CAT_NONE:
            if local_cat != CAT_SPACE:
                cat = local_cat
        elif local_cat != cat:
            return i
    else:
        return len(text)
