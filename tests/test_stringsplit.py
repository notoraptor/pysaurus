import unicodedata

from pysaurus.core.stringsplit import get_next_word_position, get_previous_word_position


def _debug(text: str):
    for i, c in enumerate(text):
        print(i, c, unicodedata.category(c))
    print("----")


def test_string_split_left():
    string = "abc10_ !@$##$%^&*()_+-=[]\{}|;':,./<>?"
    split_positions = []
    pos = len(string)
    print()
    while True:
        next_pos = get_previous_word_position(string, pos)
        print(f"{next_pos}:", string[next_pos:])
        split_positions.append(next_pos)
        if next_pos:
            pos = next_pos - 1
        else:
            break
    assert split_positions == [20, 19, 13, 12, 10, 9, 7, 0]


def test_string_split_right():
    string = "abc10_ !@$##$%^&*()_+-=[]\{}|;':,./<>?"
    split_positions = []
    pos = 0
    print()
    while True:
        next_pos = get_next_word_position(string, pos)
        print(f"{next_pos}:", string[next_pos:])
        split_positions.append(next_pos)
        if next_pos < len(string):
            pos = next_pos
        else:
            break
    assert split_positions == [6, 9, 10, 12, 13, 19, 20, 38]
