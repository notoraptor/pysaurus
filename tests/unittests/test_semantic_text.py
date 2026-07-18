from pysaurus.core.semantic_text import CharClass, SemanticText, encode_numbers_for_sort


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


class TestEncodeNumbersForSort:
    def test_digit_run_becomes_length_prefixed_key(self):
        assert encode_numbers_for_sort("file2") == "file 000012 "
        assert encode_numbers_for_sort("e100") == "e 00003100 "

    def test_sort_is_natural_without_any_global_padding(self):
        items = ["file2", "file10", "file1"]
        result = sorted(items, key=encode_numbers_for_sort)
        assert result == ["file1", "file2", "file10"]

    def test_longer_number_added_later_still_sorts_correctly(self):
        # The old fixed-padding scheme broke as soon as a number longer than
        # the padding appeared; the length prefix is per-value and cannot.
        items = ["e2", "e100"]
        assert sorted(items, key=encode_numbers_for_sort) == ["e2", "e100"]
        items.append("e10000000")
        assert sorted(items, key=encode_numbers_for_sort) == ["e2", "e100", "e10000000"]

    def test_leading_zeros_compare_equal_to_plain_number(self):
        assert encode_numbers_for_sort("e007") == encode_numbers_for_sort("e7")
        assert encode_numbers_for_sort("v000") == encode_numbers_for_sort("v0")

    def test_zero_stripping_beats_textual_length(self):
        # "07" has more characters than "8" but is the smaller number.
        assert encode_numbers_for_sort("e07") < encode_numbers_for_sort("e8")

    def test_numbers_sort_before_other_characters(self):
        # The leading space of the key ranks digit runs before any printable.
        items = ["a!", "a1", "a b"]
        assert sorted(items, key=encode_numbers_for_sort) == ["a1", "a b", "a!"]

    def test_superscript_digits_converted(self):
        # x² -> x 000012
        assert encode_numbers_for_sort("x\u00b2") == "x 000012 "

    def test_subscript_digits_converted(self):
        # H₁₂ -> H 0000212
        assert encode_numbers_for_sort("H\u2081\u2082") == "H 0000212 "

    def test_multiple_spaces_collapsed(self):
        assert "  " not in encode_numbers_for_sort("a  1  b")

    def test_order_matches_semantic_text(self):
        # Same lowercase corpus sorted by encoded key and by SemanticText
        # comparison must agree (case handling is where the two differ on
        # purpose: SQL sorting compares letters byte-wise).
        corpus = [
            "e1",
            "e2",
            "e10",
            "e100",
            "e007",
            "e9",
            "s2e10",
            "s2e2",
            "s10e1",
            "episode 9.mkv",
            "episode 10.mkv",
            "part1000",
            "part999",
            "0",
            "42",
        ]
        by_key = sorted(corpus, key=encode_numbers_for_sort)
        by_semantic = [st.value for st in sorted(SemanticText(f) for f in corpus)]
        assert by_key == by_semantic
