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
            pos = next_pos
        else:
            break
    assert split_positions == [20, 19, 13, 12, 10, 9, 7, 0]


def test_string_split_left_reverse():
    string = "".join(reversed("abc10_ !@$##$%^&*()_+-=[]\{}|;':,./<>?"))
    split_positions = []
    pos = 0
    print()
    while True:
        next_pos = get_next_word_position(string, pos)
        print(f"{next_pos}:", string[next_pos:])
        split_positions.append(len(string) - next_pos)
        if next_pos < len(string):
            pos = next_pos
        else:
            break
    assert split_positions == [20, 19, 13, 12, 10, 9, 7, 0]


def test_string_split_left_simple():
    string = "Hello world, how are you "
    assert len(string) == 25

    prev_pos = get_previous_word_position(string, len(string))
    assert string[prev_pos:] == "you "
    assert prev_pos == 21

    prev_pos = get_previous_word_position(string, prev_pos)
    assert string[prev_pos:] == "are you "
    assert prev_pos == 17

    prev_pos = get_previous_word_position(string, prev_pos)
    assert string[prev_pos:] == "how are you "
    assert prev_pos == 13

    prev_pos = get_previous_word_position(string, prev_pos)
    assert string[prev_pos:] == ", how are you "
    assert prev_pos == 11

    prev_pos = get_previous_word_position(string, prev_pos)
    assert string[prev_pos:] == "world, how are you "
    assert prev_pos == 6

    prev_pos = get_previous_word_position(string, prev_pos)
    assert string[prev_pos:] == "Hello world, how are you "
    assert prev_pos == 0


def test_string_split_left_simple_with_end():
    string = "Hello world, how are you ?"
    assert len(string) == 26

    prev_pos = get_previous_word_position(string, len(string))
    assert string[prev_pos:] == "?"
    assert prev_pos == 25

    prev_pos = get_previous_word_position(string, prev_pos)
    assert string[prev_pos:] == "you ?"
    assert prev_pos == 21

    prev_pos = get_previous_word_position(string, prev_pos)
    assert string[prev_pos:] == "are you ?"
    assert prev_pos == 17

    prev_pos = get_previous_word_position(string, prev_pos)
    assert string[prev_pos:] == "how are you ?"
    assert prev_pos == 13

    prev_pos = get_previous_word_position(string, prev_pos)
    assert string[prev_pos:] == ", how are you ?"
    assert prev_pos == 11

    prev_pos = get_previous_word_position(string, prev_pos)
    assert string[prev_pos:] == "world, how are you ?"
    assert prev_pos == 6

    prev_pos = get_previous_word_position(string, prev_pos)
    assert string[prev_pos:] == "Hello world, how are you ?"
    assert prev_pos == 0


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
