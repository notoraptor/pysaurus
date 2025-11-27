import pytest

from pysaurus.core.file_size import FileSize


class TestFileSizeFormatting:
    def test_format_zero(self):
        assert str(FileSize(0)) == "0.0 b"

    def test_format_bytes(self):
        assert str(FileSize(1)) == "1.0 b"
        assert str(FileSize(512)) == "512.0 b"
        assert str(FileSize(1023)) == "1023.0 b"

    def test_format_kilobytes(self):
        assert str(FileSize(1024)) == "1.0 KiB"
        assert str(FileSize(1536)) == "1.5 KiB"  # 1.5 * 1024
        assert str(FileSize(2048)) == "2.0 KiB"
        assert str(FileSize(10240)) == "10.0 KiB"

    def test_format_megabytes(self):
        assert str(FileSize(1048576)) == "1.0 MiB"  # 1024 * 1024
        assert str(FileSize(1572864)) == "1.5 MiB"  # 1.5 * 1024 * 1024
        assert str(FileSize(5242880)) == "5.0 MiB"  # 5 * 1024 * 1024

    def test_format_gigabytes(self):
        assert str(FileSize(1073741824)) == "1.0 GiB"  # 1024^3
        assert str(FileSize(2147483648)) == "2.0 GiB"  # 2 * 1024^3
        assert str(FileSize(5368709120)) == "5.0 GiB"  # 5 * 1024^3

    def test_format_terabytes(self):
        assert str(FileSize(1099511627776)) == "1.0 TiB"  # 1024^4
        assert str(FileSize(2199023255552)) == "2.0 TiB"  # 2 * 1024^4

    def test_format_with_decimals(self):
        assert str(FileSize(1280)) == "1.25 KiB"  # 1.25 * 1024
        assert str(FileSize(2560)) == "2.5 KiB"  # 2.5 * 1024
        assert str(FileSize(2621440)) == "2.5 MiB"  # 2.5 * 1024 * 1024

    def test_format_rounding(self):
        # Should round to 2 decimal places
        assert str(FileSize(1331)) == "1.3 KiB"  # 1331/1024 ≈ 1.2998
        assert str(FileSize(1434)) == "1.4 KiB"  # 1434/1024 = 1.4004
        assert str(FileSize(1638)) == "1.6 KiB"  # 1638/1024 ≈ 1.5996

    def test_format_negative_values(self):
        assert str(FileSize(-1)) == "-1.0 b"
        assert str(FileSize(-512)) == "-512.0 b"
        assert str(FileSize(-1024)) == "-1.0 KiB"
        assert str(FileSize(-1536)) == "-1.5 KiB"
        assert str(FileSize(-1048576)) == "-1.0 MiB"
        assert str(FileSize(-1073741824)) == "-1.0 GiB"

    def test_format_boundary_values(self):
        # Just under next unit threshold
        assert str(FileSize(1023)) == "1023.0 b"
        assert str(FileSize(1048575)) == "1024.0 KiB"  # (1024*1024-1)/1024

        # Just at unit boundary
        assert str(FileSize(1024)) == "1.0 KiB"
        assert str(FileSize(1048576)) == "1.0 MiB"


class TestFileSizeComparison:
    def test_equality(self):
        fs1 = FileSize(1024)
        fs2 = FileSize(1024)
        fs3 = FileSize(2048)

        assert fs1 == fs2
        assert not (fs1 == fs3)
        assert fs1 != fs3
        assert not (fs1 != fs2)

    def test_less_than(self):
        fs1 = FileSize(1024)
        fs2 = FileSize(2048)

        assert fs1 < fs2
        assert not (fs2 < fs1)
        assert not (fs1 < fs1)

    def test_greater_than(self):
        fs1 = FileSize(1024)
        fs2 = FileSize(2048)

        assert fs2 > fs1
        assert not (fs1 > fs2)
        assert not (fs1 > fs1)

    def test_less_equal(self):
        fs1 = FileSize(1024)
        fs2 = FileSize(2048)
        fs3 = FileSize(1024)

        assert fs1 <= fs2
        assert fs1 <= fs3
        assert not (fs2 <= fs1)

    def test_greater_equal(self):
        fs1 = FileSize(1024)
        fs2 = FileSize(2048)
        fs3 = FileSize(1024)

        assert fs2 >= fs1
        assert fs1 >= fs3
        assert not (fs1 >= fs2)

    def test_comparison_with_negatives(self):
        fs1 = FileSize(-2048)
        fs2 = FileSize(-1024)
        fs3 = FileSize(0)
        fs4 = FileSize(1024)

        # Negative values should be less than positive
        assert fs1 < fs2 < fs3 < fs4
        assert fs4 > fs3 > fs2 > fs1
        assert fs1 != fs4

    def test_comparison_with_non_filesize(self):
        fs = FileSize(1024)

        # Comparisons with non-FileSize should return False
        assert not (fs == 1024)
        assert not (fs != 1024)
        assert not (fs < 1024)
        assert not (fs > 1024)
        assert not (fs <= 1024)
        assert not (fs >= 1024)

    def test_sorting(self):
        sizes = [
            FileSize(2048),
            FileSize(-1024),
            FileSize(0),
            FileSize(1048576),
            FileSize(-2048),
            FileSize(512),
        ]

        # Sort using the FileSize objects directly
        sorted_sizes = sorted(sizes)

        # Verify order by string representation
        expected_order = [
            "-2.0 KiB",  # -2048
            "-1.0 KiB",  # -1024
            "0.0 b",  # 0
            "512.0 b",  # 512
            "2.0 KiB",  # 2048
            "1.0 MiB",  # 1048576
        ]

        assert [str(fs) for fs in sorted_sizes] == expected_order


class TestFileSizeHashing:
    def test_hash_equality(self):
        fs1 = FileSize(1024)
        fs2 = FileSize(1024)
        fs3 = FileSize(2048)

        # Same value should have same hash
        assert hash(fs1) == hash(fs2)
        # Different values should (likely) have different hashes
        assert hash(fs1) != hash(fs3)

    def test_hash_with_negatives(self):
        fs1 = FileSize(1024)
        fs2 = FileSize(-1024)

        # Positive and negative should have different hashes
        assert hash(fs1) != hash(fs2)

    def test_can_use_as_dict_key(self):
        fs1 = FileSize(1024)
        fs2 = FileSize(1024)
        fs3 = FileSize(2048)
        fs4 = FileSize(-1024)

        d = {fs1: "first", fs3: "second", fs4: "third"}

        # fs2 should map to same value as fs1 (same hash/equality)
        assert d[fs2] == "first"
        assert d[fs3] == "second"
        assert d[fs4] == "third"

    def test_can_use_in_set(self):
        fs1 = FileSize(1024)
        fs2 = FileSize(1024)
        fs3 = FileSize(2048)
        fs4 = FileSize(-1024)

        s = {fs1, fs2, fs3, fs4}

        # fs1 and fs2 are equal, so set should have 3 items
        assert len(s) == 3

        # Verify the items in the set
        assert FileSize(1024) in s
        assert FileSize(2048) in s
        assert FileSize(-1024) in s
        assert FileSize(4096) not in s


class TestFileSizeConstants:
    def test_base_constants(self):
        assert FileSize.BYTES == 1
        assert FileSize.KILO_BYTES == 1024
        assert FileSize.MEGA_BYTES == 1024 * 1024
        assert FileSize.GIGA_BYTES == 1024 * 1024 * 1024
        assert FileSize.TERA_BYTES == 1024 * 1024 * 1024 * 1024

    def test_bases_list(self):
        assert FileSize.BASES == [
            1,  # BYTES
            1024,  # KILO_BYTES
            1048576,  # MEGA_BYTES
            1073741824,  # GIGA_BYTES
            1099511627776,  # TERA_BYTES
        ]

    def test_names_list(self):
        assert FileSize.NAMES == ["b", "KiB", "MiB", "GiB", "TiB"]

    def test_constants_consistency(self):
        # Verify that BASES corresponds to the individual constants
        assert FileSize.BASES[0] == FileSize.BYTES
        assert FileSize.BASES[1] == FileSize.KILO_BYTES
        assert FileSize.BASES[2] == FileSize.MEGA_BYTES
        assert FileSize.BASES[3] == FileSize.GIGA_BYTES
        assert FileSize.BASES[4] == FileSize.TERA_BYTES


class TestFileSizeEdgeCases:
    def test_zero(self):
        fs = FileSize(0)
        assert str(fs) == "0.0 b"
        assert fs == FileSize(0)
        assert hash(fs) == hash(FileSize(0))

    def test_one_byte(self):
        fs = FileSize(1)
        assert str(fs) == "1.0 b"
        assert fs == FileSize(1)

    def test_negative_one_byte(self):
        fs = FileSize(-1)
        assert str(fs) == "-1.0 b"
        assert fs == FileSize(-1)
        assert fs != FileSize(1)

    def test_very_large_value(self):
        # 1 PiB (petabyte) = 1024 TiB
        # Should display in TiB since that's our largest unit
        pib = 1125899906842624  # 1024^5
        fs = FileSize(pib)
        assert str(fs) == "1024.0 TiB"

    def test_very_large_negative(self):
        # Large negative value
        fs = FileSize(-1125899906842624)
        assert str(fs) == "-1024.0 TiB"

    def test_exact_power_of_1024(self):
        # Test exact powers of 1024
        powers_and_expected = [
            (1024**0, "1.0 b"),
            (1024**1, "1.0 KiB"),
            (1024**2, "1.0 MiB"),
            (1024**3, "1.0 GiB"),
            (1024**4, "1.0 TiB"),
        ]

        for value, expected in powers_and_expected:
            assert str(FileSize(value)) == expected
            assert str(FileSize(-value)) == f"-{expected}"

    def test_just_under_boundaries(self):
        # Test values just under unit boundaries
        assert str(FileSize(1023)) == "1023.0 b"
        assert str(FileSize(1024 * 1024 - 1)) == "1024.0 KiB"
        assert str(FileSize(1024 * 1024 * 1024 - 1)) == "1024.0 MiB"


class TestFileSizeImmutability:
    def test_string_representation_consistent(self):
        fs = FileSize(1536)

        # Multiple calls to str() should return the same value
        str1 = str(fs)
        str2 = str(fs)
        assert str1 == str2 == "1.5 KiB"

    def test_hash_consistent(self):
        fs = FileSize(1024)

        # Multiple calls to hash() should return the same value
        hash1 = hash(fs)
        hash2 = hash(fs)
        assert hash1 == hash2


@pytest.mark.parametrize(
    "size,expected",
    [
        # Bytes range
        (0, "0.0 b"),
        (1, "1.0 b"),
        (512, "512.0 b"),
        (1023, "1023.0 b"),
        # KiB range
        (1024, "1.0 KiB"),
        (1536, "1.5 KiB"),
        (2048, "2.0 KiB"),
        (1048575, "1024.0 KiB"),
        # MiB range
        (1048576, "1.0 MiB"),
        (1572864, "1.5 MiB"),
        (5242880, "5.0 MiB"),
        # GiB range
        (1073741824, "1.0 GiB"),
        (1610612736, "1.5 GiB"),
        # TiB range
        (1099511627776, "1.0 TiB"),
        # Negative values
        (-1024, "-1.0 KiB"),
        (-1048576, "-1.0 MiB"),
    ],
)
def test_parametrized_formatting(size, expected):
    assert str(FileSize(size)) == expected


@pytest.mark.parametrize(
    "size1,size2,expected_lt,expected_eq",
    [
        (0, 0, False, True),
        (0, 1, True, False),
        (1, 0, False, False),
        (1024, 1024, False, True),
        (1024, 2048, True, False),
        (-1024, 0, True, False),
        (-1024, 1024, True, False),
        (-2048, -1024, True, False),
    ],
)
def test_parametrized_comparison(size1, size2, expected_lt, expected_eq):
    fs1 = FileSize(size1)
    fs2 = FileSize(size2)

    assert (fs1 < fs2) is expected_lt
    assert (fs1 == fs2) is expected_eq
    assert (fs1 > fs2) is (not expected_lt and not expected_eq)
