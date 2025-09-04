from datetime import timedelta

import pytest

from pysaurus.core.duration import Duration, ShortDuration


class TestDurationInitialization:
    def test_init_with_integer(self):
        d = Duration(1_000_000)
        assert d.t == 1_000_000
        assert d.d == 0
        assert d.h == 0
        assert d.m == 0
        assert d.s == 1
        assert d.u == 0

    def test_init_with_float_rounds_correctly(self):
        d1 = Duration(1_500_000.4)
        assert d1.t == 1_500_000
        assert d1.s == 1
        assert d1.u == 500_000

        d2 = Duration(1_500_000.6)
        assert d2.t == 1_500_001
        assert d2.s == 1
        assert d2.u == 500_001

    def test_init_with_zero(self):
        d = Duration(0)
        assert d.t == 0
        assert d.d == 0
        assert d.h == 0
        assert d.m == 0
        assert d.s == 0
        assert d.u == 0

    def test_init_with_negative_value(self):
        d = Duration(-1_000_000)
        assert d.t == -1_000_000
        assert d.sign == -1
        assert d.s == 1  # Decomposition should be positive
        assert d.u == 0
        assert str(d) == "-01s"

    def test_init_with_negative_complex(self):
        # -1 day, 2 hours, 3 minutes, 4 seconds, 567890 microseconds
        microseconds = -(
            86_400_000_000
            + 2 * 3_600_000_000
            + 3 * 60_000_000
            + 4 * 1_000_000
            + 567_890
        )
        d = Duration(microseconds)
        assert d.sign == -1
        assert d.d == 1  # All parts should be positive
        assert d.h == 2
        assert d.m == 3
        assert d.s == 4
        assert d.u == 567_890
        assert str(d) == "-01d 02h 03m 04s 567890µs"

    def test_negative_rounding(self):
        d1 = Duration(-1_500_000.4)
        assert d1.t == -1_500_000
        assert d1.sign == -1

        d2 = Duration(-1_500_000.6)
        assert d2.t == -1_500_001
        assert d2.sign == -1

    def test_decomposition_days(self):
        d = Duration(86_400_000_000)
        assert d.d == 1
        assert d.h == 0
        assert d.m == 0
        assert d.s == 0
        assert d.u == 0

    def test_decomposition_hours(self):
        d = Duration(3_600_000_000)
        assert d.d == 0
        assert d.h == 1
        assert d.m == 0
        assert d.s == 0
        assert d.u == 0

    def test_decomposition_minutes(self):
        d = Duration(60_000_000)
        assert d.d == 0
        assert d.h == 0
        assert d.m == 1
        assert d.s == 0
        assert d.u == 0

    def test_decomposition_complex(self):
        # 1 day, 2 hours, 3 minutes, 4 seconds, 567890 microseconds
        microseconds = (
            86_400_000_000
            + 2 * 3_600_000_000
            + 3 * 60_000_000
            + 4 * 1_000_000
            + 567_890
        )
        d = Duration(microseconds)
        assert d.d == 1
        assert d.h == 2
        assert d.m == 3
        assert d.s == 4
        assert d.u == 567_890


class TestDurationFactoryMethods:
    def test_from_seconds(self):
        d = Duration.from_seconds(30)
        assert d.t == 30_000_000
        assert d.s == 30
        assert d.u == 0

    def test_from_seconds_with_float(self):
        d = Duration.from_seconds(30.5)
        assert d.t == 30_500_000
        assert d.s == 30
        assert d.u == 500_000

    def test_from_minutes(self):
        d = Duration.from_minutes(5)
        assert d.t == 300_000_000
        assert d.m == 5
        assert d.s == 0

    def test_from_minutes_with_float(self):
        d = Duration.from_minutes(1.5)
        assert d.t == 90_000_000
        assert d.m == 1
        assert d.s == 30

    def test_from_timedelta_simple(self):
        td = timedelta(seconds=30)
        d = Duration.from_timedelta(td)
        assert d.t == 30_000_000
        assert d.s == 30
        assert d.u == 0

    def test_from_timedelta_with_microseconds(self):
        td = timedelta(seconds=30, microseconds=500_000)
        d = Duration.from_timedelta(td)
        assert d.t == 30_500_000
        assert d.s == 30
        assert d.u == 500_000

    def test_from_timedelta_complex(self):
        td = timedelta(days=1, hours=2, minutes=3, seconds=4, microseconds=567_890)
        d = Duration.from_timedelta(td)
        assert d.d == 1
        assert d.h == 2
        assert d.m == 3
        assert d.s == 4
        assert d.u == 567_890

    def test_from_timedelta_zero(self):
        td = timedelta()
        d = Duration.from_timedelta(td)
        assert d.t == 0
        assert str(d) == "00s"

    def test_from_timedelta_negative(self):
        td = timedelta(seconds=-5)
        d = Duration.from_timedelta(td)
        assert d.t == -5_000_000
        assert str(d) == "-05s"

    def test_from_seconds_negative(self):
        d = Duration.from_seconds(-30.5)
        assert d.t == -30_500_000
        assert d.sign == -1
        assert d.s == 30
        assert d.u == 500_000
        assert str(d) == "-30s 500000µs"

    def test_from_minutes_negative(self):
        d = Duration.from_minutes(-1.5)
        assert d.t == -90_000_000
        assert d.sign == -1
        assert d.m == 1
        assert d.s == 30
        assert str(d) == "-01m 30s"

    def test_from_timedelta_one_microsecond(self):
        td = timedelta(microseconds=1)
        d = Duration.from_timedelta(td)
        assert d.t == 1
        assert d.u == 1

    def test_from_timedelta_fractional_microseconds(self):
        # timedelta with 1.5 seconds = 1,500,000 microseconds
        td = timedelta(seconds=1.5)
        d = Duration.from_timedelta(td)
        assert d.t == 1_500_000
        assert d.s == 1
        assert d.u == 500_000

    def test_from_timedelta_precision_preservation(self):
        # Test that microsecond precision is preserved through the conversion
        td = timedelta(microseconds=123_456)
        d = Duration.from_timedelta(td)
        assert d.t == 123_456
        assert d.u == 123_456


class TestDurationComparison:
    def test_equality(self):
        d1 = Duration(1_000_000)
        d2 = Duration(1_000_000)
        d3 = Duration(2_000_000)

        assert d1 == d2
        assert not d1 == d3
        assert d1 != d3
        assert not d1 != d2

    def test_less_than(self):
        d1 = Duration(1_000_000)
        d2 = Duration(2_000_000)

        assert d1 < d2
        assert not d2 < d1
        assert not d1 < d1

    def test_greater_than(self):
        d1 = Duration(1_000_000)
        d2 = Duration(2_000_000)

        assert d2 > d1
        assert not d1 > d2
        assert not d1 > d1

    def test_less_equal(self):
        d1 = Duration(1_000_000)
        d2 = Duration(2_000_000)
        d3 = Duration(1_000_000)

        assert d1 <= d2
        assert d1 <= d3
        assert not d2 <= d1

    def test_greater_equal(self):
        d1 = Duration(1_000_000)
        d2 = Duration(2_000_000)
        d3 = Duration(1_000_000)

        assert d2 >= d1
        assert d1 >= d3
        assert not d1 >= d2

    def test_sorting(self):
        durations = [
            Duration(3_000_000),
            Duration(1_000_000),
            Duration(2_000_000),
        ]
        sorted_durations = sorted(durations)

        assert sorted_durations[0].t == 1_000_000
        assert sorted_durations[1].t == 2_000_000
        assert sorted_durations[2].t == 3_000_000

    def test_comparison_with_negatives(self):
        d1 = Duration(-5_000_000)
        d2 = Duration(-2_000_000)
        d3 = Duration(3_000_000)

        # Negative comparisons
        assert d1 < d2 < d3
        assert d3 > d2 > d1
        assert d1 != d3

    def test_sorting_with_negatives(self):
        durations = [
            Duration(3_000_000),
            Duration(-5_000_000),
            Duration(0),
            Duration(-2_000_000),
            Duration(1_000_000),
        ]
        sorted_durations = sorted(durations)

        assert sorted_durations[0].t == -5_000_000
        assert sorted_durations[1].t == -2_000_000
        assert sorted_durations[2].t == 0
        assert sorted_durations[3].t == 1_000_000
        assert sorted_durations[4].t == 3_000_000


class TestDurationHashing:
    def test_hash_equality(self):
        d1 = Duration(1_000_000)
        d2 = Duration(1_000_000)
        d3 = Duration(2_000_000)

        assert hash(d1) == hash(d2)
        assert hash(d1) != hash(d3)

    def test_can_use_as_dict_key(self):
        d1 = Duration(1_000_000)
        d2 = Duration(1_000_000)
        d3 = Duration(2_000_000)

        d = {d1: "first", d3: "second"}
        assert d[d2] == "first"
        assert d[d3] == "second"

    def test_can_use_in_set(self):
        d1 = Duration(1_000_000)
        d2 = Duration(1_000_000)
        d3 = Duration(2_000_000)

        s = {d1, d2, d3}
        assert len(s) == 2


class TestDurationStringFormatting:
    def test_str_zero(self):
        d = Duration(0)
        assert str(d) == "00s"

    def test_str_microseconds_only(self):
        d = Duration(123_456)
        assert str(d) == "123456µs"

    def test_str_seconds_only(self):
        d = Duration(5_000_000)
        assert str(d) == "05s"

    def test_str_minutes_only(self):
        d = Duration(120_000_000)
        assert str(d) == "02m"

    def test_str_hours_only(self):
        d = Duration(7_200_000_000)
        assert str(d) == "02h"

    def test_str_days_only(self):
        d = Duration(172_800_000_000)
        assert str(d) == "02d"

    def test_str_seconds_and_microseconds(self):
        d = Duration(5_123_456)
        assert str(d) == "05s 123456µs"

    def test_str_minutes_and_seconds(self):
        d = Duration(65_000_000)
        assert str(d) == "01m 05s"

    def test_str_hours_minutes_seconds(self):
        d = Duration(3_665_000_000)
        assert str(d) == "01h 01m 05s"

    def test_str_complex(self):
        # 1 day, 2 hours, 3 minutes, 4 seconds, 567890 microseconds
        microseconds = (
            86_400_000_000
            + 2 * 3_600_000_000
            + 3 * 60_000_000
            + 4 * 1_000_000
            + 567_890
        )
        d = Duration(microseconds)
        assert str(d) == "01d 02h 03m 04s 567890µs"

    def test_str_skips_zero_units(self):
        # 1 hour and 5 seconds (no minutes)
        d = Duration(3_605_000_000)
        assert str(d) == "01h 05s"


class TestShortDuration:
    def test_short_duration_seconds_only(self):
        d = ShortDuration(45_000_000)
        assert str(d) == "00:00:45"

    def test_short_duration_minutes_seconds(self):
        d = ShortDuration(125_000_000)
        assert str(d) == "00:02:05"

    def test_short_duration_hours_minutes_seconds(self):
        d = ShortDuration(3_665_000_000)
        assert str(d) == "01:01:05"

    def test_short_duration_with_days(self):
        # 1 day, 2 hours, 3 minutes, 4 seconds
        microseconds = (
            86_400_000_000 + 2 * 3_600_000_000 + 3 * 60_000_000 + 4 * 1_000_000
        )
        d = ShortDuration(microseconds)
        assert str(d) == "01d:02:03:04"

    def test_short_duration_rounds_microseconds(self):
        # 30 seconds + 600,000 microseconds = 30.6 seconds -> rounds to 31
        d = ShortDuration(30_600_000)
        assert str(d) == "00:00:31"

    def test_short_duration_rounds_down(self):
        # 30 seconds + 400,000 microseconds = 30.4 seconds -> rounds to 30
        d = ShortDuration(30_400_000)
        assert str(d) == "00:00:30"

    def test_short_duration_zero(self):
        d = ShortDuration(0)
        assert str(d) == "00:00:00"

    def test_short_duration_inherits_comparison(self):
        d1 = ShortDuration(1_000_000)
        d2 = ShortDuration(2_000_000)
        assert d1 < d2
        assert d2 > d1
        assert d1 == ShortDuration(1_000_000)

    def test_short_duration_factory_methods(self):
        d1 = ShortDuration.from_seconds(90)
        assert str(d1) == "00:01:30"

        d2 = ShortDuration.from_minutes(75)
        assert str(d2) == "01:15:00"

    def test_short_duration_from_timedelta(self):
        td = timedelta(hours=1, minutes=30, seconds=45)
        d = ShortDuration.from_timedelta(td)
        assert str(d) == "01:30:45"

    def test_short_duration_from_timedelta_with_days(self):
        td = timedelta(days=2, hours=3, minutes=15, seconds=30)
        d = ShortDuration.from_timedelta(td)
        assert str(d) == "02d:03:15:30"

    def test_short_duration_negative(self):
        d = ShortDuration(-65_000_000)
        assert d.sign == -1
        assert d.m == 1
        assert d.s == 5
        assert str(d) == "-00:01:05"

    def test_short_duration_negative_with_days(self):
        microseconds = -(86_400_000_000 + 3_600_000_000 + 60_000_000 + 30_000_000)
        d = ShortDuration(microseconds)
        assert d.sign == -1
        assert str(d) == "-01d:01:01:30"


class TestEdgeCases:
    def test_very_large_duration(self):
        # 365 days
        d = Duration(365 * 86_400_000_000)
        assert d.d == 365
        assert str(d) == "365d"

    def test_max_microseconds(self):
        # 999,999 microseconds (just under 1 second)
        d = Duration(999_999)
        assert d.s == 0
        assert d.u == 999_999
        assert str(d) == "999999µs"

    def test_one_microsecond(self):
        d = Duration(1)
        assert d.u == 1
        assert str(d) == "000001µs"

    def test_float_precision_edge_case(self):
        # Test that float values very close to .5 round correctly
        d1 = Duration(1_000_000.5)
        assert d1.t == 1_000_000  # Should round to even

        d2 = Duration(1_000_001.5)
        assert d2.t == 1_000_002  # Should round to even

    @pytest.mark.parametrize(
        "value",
        [
            0,
            1,
            999_999,
            1_000_000,
            60_000_000,
            3_600_000_000,
            86_400_000_000,
        ],
    )
    def test_various_values(self, value):
        d = Duration(value)
        assert isinstance(d.t, int)
        assert d.t == round(value)
