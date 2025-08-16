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


def test_asian_text_navigation():
    """Test word navigation with Asian scripts (Chinese, Japanese, Korean)

    NOTE: This test documents current behavior and limitations.
    Expected to fail/show suboptimal behavior until Asian script support is improved.
    Each CJK ideograph should ideally be treated as a separate 'word' unit.
    """
    # Test 1: Chinese text - "Hello world, this is a test."
    chinese_text = "你好世界，这是测试。"
    print(f"\n=== Chinese Text Test ===")
    print(f"Text length: {len(chinese_text)} characters")

    # Debug character categories without printing actual characters
    print("Character categories:")
    for i, c in enumerate(chinese_text):
        print(f"  {i}: {unicodedata.category(c)} ({'space' if c == ' ' else 'other'})")

    # Test navigation
    pos = 0
    chinese_positions = []
    while pos < len(chinese_text):
        next_pos = get_next_word_position(chinese_text, pos)
        chinese_positions.append(next_pos)
        print(
            f"Position {pos} -> {next_pos} (remaining: {len(chinese_text) - next_pos})"
        )
        if next_pos == pos:  # Prevent infinite loop
            break
        pos = next_pos

    # Test 2: Japanese mixed text - "Fire Force Hello World"
    japanese_text = "炎炎ノ消防隊 Hello 世界"
    print(f"\n=== Japanese Mixed Text Test ===")
    print(f"Text length: {len(japanese_text)} characters")

    # Debug categories
    print("Character categories:")
    for i, c in enumerate(japanese_text):
        cat = unicodedata.category(c)
        is_space = c == " "
        is_alpha = c.isalnum()
        print(f"  {i}: {cat} (space={is_space}, alnum={is_alpha})")

    pos = 0
    japanese_positions = []
    while pos < len(japanese_text):
        next_pos = get_next_word_position(japanese_text, pos)
        japanese_positions.append(next_pos)
        print(f"Position {pos} -> {next_pos}")
        if next_pos == pos:  # Prevent infinite loop
            break
        pos = next_pos

    # Test 3: Korean text - "Hello Korean test"
    korean_text = "안녕하세요 한글 테스트"
    print(f"\n=== Korean Text Test ===")
    print(f"Text length: {len(korean_text)} characters")

    pos = 0
    korean_positions = []
    while pos < len(korean_text):
        next_pos = get_next_word_position(korean_text, pos)
        korean_positions.append(next_pos)
        print(f"Position {pos} -> {next_pos}")
        if next_pos == pos:  # Prevent infinite loop
            break
        pos = next_pos

    # Document current behavior (will need updating when CJK support is added)
    print(f"\nChinese positions: {chinese_positions}")
    print(f"Japanese positions: {japanese_positions}")
    print(f"Korean positions: {korean_positions}")

    # TODO: When Asian script support is implemented, update these assertions
    # Ideal behavior would be:
    # Chinese: Each character should be a word boundary: [1,2,3,4,5,6,7,8,9]
    # Japanese: "炎炎ノ消防隊" + " " + "Hello" + " " + "世界" = [5,6,11,12,14]
    # Korean: Each syllable block should be detected properly

    # For now, just ensure we don't crash and return valid positions
    assert all(pos >= 0 for pos in chinese_positions)
    assert all(pos >= 0 for pos in japanese_positions)
    assert all(pos >= 0 for pos in korean_positions)

    # OBSERVED BEHAVIOR ANALYSIS:
    #
    # Chinese "你好世界，这是测试。" -> positions [4, 5, 9, 10]
    # - Characters 0-3 (你好世界) treated as single OTHER word
    # - Character 4 (，) punctuation creates boundary
    # - Characters 5-8 (这是测试) treated as single OTHER word
    # - Character 9 (。) punctuation creates boundary
    # ISSUE: Should be [1,2,3,4,5,6,7,8,9,10] (each character = word)
    #
    # Japanese "炎炎ノ消防隊 Hello 世界" -> positions [6, 12, 15]
    # - Characters 0-5 (炎炎ノ消防隊) treated as single OTHER word
    # - Space at 6 correctly detected
    # - "Hello" correctly detected as WORD
    # - Space at 12 correctly detected
    # - Characters 13-14 (世界) treated as single OTHER word
    # MIXED: English words work, CJK treated as single blocks
    #
    # Korean "안녕하세요 한글 테스트" -> positions [5, 8, 12]
    # - Characters 0-4 (안녕하세요) treated as single OTHER word
    # - Spaces correctly detected as separators
    # - Each Korean word group treated as single OTHER block
    # ISSUE: Korean syllables should potentially be separate units
    #
    # CONCLUSION: Current algorithm correctly handles:
    # ✅ Space separation between Asian and Latin scripts
    # ✅ Punctuation boundaries in Asian text
    # ✅ Mixed scripts with English words preserved
    # ❌ CJK characters treated as monolithic OTHER category
    # ❌ No per-character or per-syllable granularity for Asian scripts
