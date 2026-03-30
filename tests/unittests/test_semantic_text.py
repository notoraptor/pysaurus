from pysaurus.core.semantic_text import (
    CharClass,
    SemanticText,
    get_longest_number_in_string,
    pad_numbers_in_string,
)


class TestSemanticTextNaturalSort:
    """SemanticText sorts strings with embedded numbers in natural order."""

    def test_numbers_sort_by_value_not_lexicographic(self):
        assert SemanticText("file2") < SemanticText("file10")

    def test_identical_strings_are_equal(self):
        assert SemanticText("abc") == SemanticText("abc")
        assert not SemanticText("abc") < SemanticText("abc")

    def test_case_insensitive_ordering(self):
        # 'a' and 'A' compare equal on lower_rank, uppercase wins tiebreak
        assert SemanticText("Apple") < SemanticText("apple")
        assert SemanticText("apple") > SemanticText("Apple")

    def test_case_insensitive_with_different_letters(self):
        # 'Z' (uppercase) should sort after 'a' (lowercase) because z > a
        assert SemanticText("zebra") > SemanticText("apple")
        assert SemanticText("Zebra") > SemanticText("apple")

    def test_multiple_numbers(self):
        items = [
            SemanticText("s2e10"),
            SemanticText("s2e2"),
            SemanticText("s10e1"),
            SemanticText("s1e9"),
        ]
        result = [st.value for st in sorted(items)]
        assert result == ["s1e9", "s2e2", "s2e10", "s10e1"]

    def test_number_before_letter_in_mixed_comparison(self):
        # When types differ, int comes before CharClass
        assert SemanticText("1abc") < SemanticText("abc")

    def test_shorter_string_is_lesser(self):
        assert SemanticText("file") < SemanticText("file1")

    def test_longer_string_is_greater(self):
        assert not SemanticText("file1") < SemanticText("file")

    def test_letter_is_greater_than_number_at_same_position(self):
        # "a" (CharClass) vs "1" (int) at position 0: letter > number
        assert not SemanticText("a") < SemanticText("1")

    def test_empty_string(self):
        assert SemanticText("") < SemanticText("a")
        assert not SemanticText("")

    def test_bool(self):
        assert SemanticText("hello")
        assert not SemanticText("")

    def test_str_repr(self):
        st = SemanticText("hello")
        assert str(st) == "hello"
        assert repr(st) == "hello"

    def test_hash(self):
        assert hash(SemanticText("abc")) == hash(SemanticText("abc"))
        assert hash(SemanticText("abc")) != hash(SemanticText("def"))

    def test_realistic_filenames(self):
        filenames = [
            "Episode 9.mkv",
            "Episode 10.mkv",
            "Episode 1.mkv",
            "Episode 2.mkv",
            "Episode 20.mkv",
        ]
        result = [st.value for st in sorted(SemanticText(f) for f in filenames)]
        assert result == [
            "Episode 1.mkv",
            "Episode 2.mkv",
            "Episode 9.mkv",
            "Episode 10.mkv",
            "Episode 20.mkv",
        ]


class TestSemanticTextUnicodeDigits:
    """SemanticText handles superscript and subscript digits."""

    def test_superscript_digits_sort_as_numbers(self):
        # x² < x¹⁰
        assert SemanticText("x\u00b2") < SemanticText("x\u00b9\u2070")

    def test_subscript_digits_sort_as_numbers(self):
        # H₂ < H₁₀
        assert SemanticText("H\u2082") < SemanticText("H\u2081\u2080")

    def test_digit_class_changes_flush_accumulator(self):
        # ASCII digit "3" followed by superscript "²" are separate numbers
        # "a3²b" → a, 3, 2, b — the change in digit class flushes 3 before accumulating ²
        assert SemanticText("a3\u00b2b") < SemanticText("a4\u00b9b")

    def test_letter_after_number_then_number_before_letter(self):
        # "3a" vs "a3": number before letter
        assert SemanticText("3a") < SemanticText("a3")
        # "a3" vs "3a": letter after number
        assert SemanticText("a3") > SemanticText("3a")


class TestCharClass:
    def test_hash_equal_for_same_char(self):
        assert hash(CharClass("a")) == hash(CharClass("a"))

    def test_is_digit_for_ascii(self):
        assert CharClass("5").is_digit()
        assert not CharClass("a").is_digit()


class TestGetLongestNumberInString:
    def test_no_numbers(self):
        assert get_longest_number_in_string("hello") == 0

    def test_single_number(self):
        assert get_longest_number_in_string("file123.txt") == 3

    def test_multiple_numbers_returns_longest(self):
        assert get_longest_number_in_string("s2e10 part1000") == 4

    def test_superscript_digits(self):
        assert get_longest_number_in_string("x\u00b2\u00b3") == 2

    def test_subscript_digits(self):
        assert get_longest_number_in_string("H\u2082O") == 1

    def test_empty_string(self):
        assert get_longest_number_in_string("") == 0


class TestPadNumbersInString:
    def test_pads_numbers_with_zeros(self):
        result = pad_numbers_in_string("file2", 4)
        assert result == "file 0002 "

    def test_padding_makes_sort_correct(self):
        items = ["file2", "file10", "file1"]
        pad = 2
        result = sorted(items, key=lambda s: pad_numbers_in_string(s, pad))
        assert result == ["file1", "file2", "file10"]

    def test_superscript_digits_converted_to_padded_numbers(self):
        # x² → x 02
        result = pad_numbers_in_string("x\u00b2", 4)
        assert "0002" in result

    def test_subscript_digits_converted_to_padded_numbers(self):
        # H₁₂ → H 0012
        result = pad_numbers_in_string("H\u2081\u2082", 4)
        assert "0012" in result

    def test_multiple_spaces_collapsed(self):
        result = pad_numbers_in_string("a  1  b", 2)
        # Numbers get padded with spaces around them; consecutive spaces collapse
        assert "  " not in result
