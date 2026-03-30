import pickle
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

import pytest

from pysaurus.core.universal_datetime import Timedelta, Timezone, UDT

UTC = Timezone()


# ============================================================
# Timezone
# ============================================================


class TestTimezoneConstruction:
    def test_utc_default(self):
        tz = Timezone()
        assert tz.microseconds == 0

    def test_positive_offset(self):
        tz = Timezone(hours=5, minutes=30)
        assert tz.microseconds == 5 * 3_600_000_000 + 30 * 60_000_000

    def test_negative_offset(self):
        tz = Timezone(hours=5, minutes=30, negative=True)
        assert tz.microseconds == -(5 * 3_600_000_000 + 30 * 60_000_000)

    def test_all_components(self):
        tz = Timezone(days=1, hours=2, minutes=3, seconds=4, microseconds=5)
        expected = (
            1 * 86_400_000_000 + 2 * 3_600_000_000 + 3 * 60_000_000 + 4 * 1_000_000 + 5
        )
        assert tz.microseconds == expected

    def test_negative_days_raises(self):
        with pytest.raises(ValueError, match="days must be >= 0"):
            Timezone(days=-1)

    def test_negative_hours_raises(self):
        with pytest.raises(ValueError, match="hours must be >= 0"):
            Timezone(hours=-1)

    def test_negative_minutes_raises(self):
        with pytest.raises(ValueError, match="minutes must be >= 0"):
            Timezone(minutes=-1)

    def test_negative_seconds_raises(self):
        with pytest.raises(ValueError, match="seconds must be >= 0"):
            Timezone(seconds=-1)

    def test_negative_microseconds_raises(self):
        with pytest.raises(ValueError, match="microseconds must be >= 0"):
            Timezone(microseconds=-1)


class TestTimezoneTzinfo:
    def test_tzname_utc(self):
        assert Timezone().tzname(None) == "UTC"

    def test_tzname_positive(self):
        assert Timezone(hours=5, minutes=30).tzname(None) == "UTC+05:30"

    def test_tzname_negative(self):
        assert Timezone(hours=3, negative=True).tzname(None) == "UTC-03:00"

    def test_tzname_with_seconds(self):
        tz = Timezone(hours=5, minutes=45, seconds=30)
        assert tz.tzname(None) == "UTC+05:45:30"

    def test_utcoffset(self):
        tz = Timezone(hours=2)
        assert tz.utcoffset(None) == timedelta(hours=2)

    def test_dst_always_zero(self):
        tz = Timezone(hours=5)
        assert tz.dst(None) == timedelta(0)


class TestTimezoneIsoformat:
    def test_utc(self):
        assert Timezone().isoformat() == "+00:00"

    def test_positive(self):
        assert Timezone(hours=5, minutes=30).isoformat() == "+05:30"

    def test_negative(self):
        assert Timezone(hours=3, negative=True).isoformat() == "-03:00"

    def test_with_seconds(self):
        assert Timezone(hours=5, minutes=45, seconds=30).isoformat() == "+05:45:30"


class TestTimezoneComparison:
    def test_equal(self):
        assert Timezone(hours=5) == Timezone(hours=5)

    def test_not_equal(self):
        assert Timezone(hours=5) != Timezone(hours=3)

    def test_lt(self):
        assert Timezone(hours=3, negative=True) < Timezone(hours=5)

    def test_gt(self):
        assert Timezone(hours=5) > Timezone(hours=3, negative=True)

    def test_le(self):
        assert Timezone(hours=5) <= Timezone(hours=5)
        assert Timezone(hours=3) <= Timezone(hours=5)

    def test_ge(self):
        assert Timezone(hours=5) >= Timezone(hours=5)
        assert Timezone(hours=5) >= Timezone(hours=3)

    def test_not_equal_to_other_type(self):
        assert Timezone(hours=5) != 42

    def test_ordering_with_other_type_raises(self):
        with pytest.raises(TypeError):
            Timezone(hours=5) < 42  # type: ignore[operator]
        with pytest.raises(TypeError):
            Timezone(hours=5) > 42  # type: ignore[operator]
        with pytest.raises(TypeError):
            Timezone(hours=5) <= 42  # type: ignore[operator]
        with pytest.raises(TypeError):
            Timezone(hours=5) >= 42  # type: ignore[operator]


class TestTimezoneHashRepr:
    def test_hash_equal_objects(self):
        assert hash(Timezone(hours=5)) == hash(Timezone(hours=5))

    def test_hash_usable_in_set(self):
        s = {Timezone(hours=5), Timezone(hours=5), Timezone(hours=3)}
        assert len(s) == 2

    def test_repr(self):
        assert repr(Timezone()) == "UTC"
        assert repr(Timezone(hours=5, minutes=30)) == "UTC+05:30"


class TestTimezoneNeg:
    def test_neg_positive(self):
        tz = -Timezone(hours=5)
        assert tz.microseconds == -(5 * 3_600_000_000)

    def test_neg_negative(self):
        tz = -Timezone(hours=5, negative=True)
        assert tz.microseconds == 5 * 3_600_000_000

    def test_neg_zero(self):
        tz = -Timezone()
        assert tz.microseconds == 0


# ============================================================
# Timedelta
# ============================================================


class TestTimedeltaConstruction:
    def test_zero(self):
        td = Timedelta()
        assert td.microseconds == 0

    def test_positive(self):
        td = Timedelta(hours=1, minutes=30)
        assert td.microseconds == 1 * 3_600_000_000 + 30 * 60_000_000

    def test_negative(self):
        td = Timedelta(seconds=90, negative=True)
        assert td.microseconds == -90_000_000

    def test_all_components(self):
        td = Timedelta(days=1, hours=2, minutes=3, seconds=4, microseconds=5)
        expected = (
            1 * 86_400_000_000 + 2 * 3_600_000_000 + 3 * 60_000_000 + 4 * 1_000_000 + 5
        )
        assert td.microseconds == expected


class TestTimedeltaStr:
    def test_zero(self):
        assert str(Timedelta()) == "00s"

    def test_all_components(self):
        td = Timedelta(days=2, hours=5, minutes=3, seconds=4, microseconds=123456)
        assert str(td) == "02d 05h 03m 04s 123456us"

    def test_hours_only(self):
        assert str(Timedelta(hours=3)) == "03h"

    def test_negative(self):
        assert str(Timedelta(seconds=90, negative=True)) == "-01m 30s"

    def test_omits_zero_components(self):
        td = Timedelta(days=1, seconds=5)
        assert str(td) == "01d 05s"


class TestTimedeltaShort:
    def test_zero(self):
        assert Timedelta().short == "00:00:00"

    def test_hours_minutes_seconds(self):
        assert Timedelta(hours=1, minutes=30, seconds=45).short == "01:30:45"

    def test_with_days(self):
        td = Timedelta(days=2, hours=3, minutes=15, seconds=30)
        assert td.short == "02d:03:15:30"

    def test_with_microseconds(self):
        td = Timedelta(hours=1, minutes=0, seconds=0, microseconds=500000)
        assert td.short == "01:00:00:500000"

    def test_negative(self):
        assert Timedelta(minutes=5, negative=True).short == "-00:05:00"


class TestTimedeltaArithmetic:
    def test_add(self):
        a = Timedelta(seconds=30)
        b = Timedelta(seconds=45)
        assert (a + b).microseconds == 75_000_000

    def test_sub(self):
        a = Timedelta(seconds=45)
        b = Timedelta(seconds=30)
        assert (a - b).microseconds == 15_000_000

    def test_sub_negative_result(self):
        a = Timedelta(seconds=30)
        b = Timedelta(seconds=45)
        result = a - b
        assert result.microseconds == -15_000_000

    def test_neg(self):
        td = Timedelta(seconds=30)
        assert (-td).microseconds == -30_000_000

    def test_add_with_other_type_raises(self):
        with pytest.raises(TypeError):
            Timedelta(seconds=1) + 42  # type: ignore[operator]

    def test_sub_with_other_type_raises(self):
        with pytest.raises(TypeError):
            Timedelta(seconds=1) - 42  # type: ignore[operator]


class TestTimedeltaConversion:
    def test_from_timedelta(self):
        td = Timedelta.from_timedelta(timedelta(hours=1, minutes=30, seconds=45))
        assert td.microseconds == (1 * 3600 + 30 * 60 + 45) * 1_000_000

    def test_from_timedelta_negative(self):
        td = Timedelta.from_timedelta(timedelta(days=-1))
        assert td.microseconds < 0

    def test_to_timedelta(self):
        td = Timedelta(hours=2, minutes=30)
        assert td.to_timedelta() == timedelta(hours=2, minutes=30)

    def test_roundtrip(self):
        original = timedelta(days=3, hours=7, minutes=15, seconds=42, microseconds=123)
        assert Timedelta.from_timedelta(original).to_timedelta() == original


class TestTimedeltaComparisonAndHash:
    def test_equal(self):
        assert Timedelta(seconds=60) == Timedelta(minutes=1)

    def test_lt(self):
        assert Timedelta(seconds=30) < Timedelta(seconds=45)

    def test_hash_equal(self):
        assert hash(Timedelta(seconds=60)) == hash(Timedelta(minutes=1))

    def test_repr(self):
        assert repr(Timedelta(seconds=90)) == "Timedelta(01m 30s)"


# ============================================================
# UDT — Construction and validation
# ============================================================


class TestUDTConstruction:
    def test_minimal(self):
        u = UDT(2024, tzinfo=UTC)
        assert u.year == 2024
        assert u.month == 1
        assert u.day == 1
        assert u.hour == 0
        assert u.minute == 0
        assert u.second == 0
        assert u.microsecond == 0
        assert u.tzinfo == UTC

    def test_full(self):
        tz = Timezone(hours=5, minutes=30)
        u = UDT(2024, 6, 15, 10, 30, 45, 123456, tz)
        assert u.year == 2024
        assert u.month == 6
        assert u.day == 15
        assert u.hour == 10
        assert u.minute == 30
        assert u.second == 45
        assert u.microsecond == 123456
        assert u.tzinfo == tz

    def test_negative_year(self):
        u = UDT(-1000, 6, 15, tzinfo=UTC)
        assert u.year == -1000

    def test_year_zero(self):
        u = UDT(0, 1, 1, tzinfo=UTC)
        assert u.year == 0

    def test_very_large_year(self):
        u = UDT(100_000, 1, 1, tzinfo=UTC)
        assert u.year == 100_000

    def test_very_negative_year(self):
        u = UDT(-100_000, 1, 1, tzinfo=UTC)
        assert u.year == -100_000

    def test_leap_year_feb_29(self):
        u = UDT(2024, 2, 29, tzinfo=UTC)
        assert u.day == 29

    def test_negative_leap_year_feb_29(self):
        # Year -400 is a leap year (divisible by 400)
        u = UDT(-400, 2, 29, tzinfo=UTC)
        assert u.day == 29


class TestUDTValidation:
    def test_month_zero(self):
        with pytest.raises(ValueError, match="month must be in 1..12"):
            UDT(2024, 0, 1, tzinfo=UTC)

    def test_month_13(self):
        with pytest.raises(ValueError, match="month must be in 1..12"):
            UDT(2024, 13, 1, tzinfo=UTC)

    def test_day_zero(self):
        with pytest.raises(ValueError, match="day must be in 1..31"):
            UDT(2024, 1, 0, tzinfo=UTC)

    def test_day_32(self):
        with pytest.raises(ValueError, match="day must be in 1..31"):
            UDT(2024, 1, 32, tzinfo=UTC)

    def test_feb_29_non_leap(self):
        with pytest.raises(ValueError, match="day must be in 1..28"):
            UDT(2023, 2, 29, tzinfo=UTC)

    def test_feb_30_leap(self):
        with pytest.raises(ValueError, match="day must be in 1..29"):
            UDT(2024, 2, 30, tzinfo=UTC)

    def test_hour_24(self):
        with pytest.raises(ValueError, match="hour must be in 0..23"):
            UDT(2024, 1, 1, 24, tzinfo=UTC)

    def test_minute_60(self):
        with pytest.raises(ValueError, match="minute must be in 0..59"):
            UDT(2024, 1, 1, 0, 60, tzinfo=UTC)

    def test_second_60(self):
        with pytest.raises(ValueError, match="second must be in 0..59"):
            UDT(2024, 1, 1, 0, 0, 60, tzinfo=UTC)

    def test_microsecond_negative(self):
        with pytest.raises(ValueError, match="microsecond must be in 0..999999"):
            UDT(2024, 1, 1, 0, 0, 0, -1, UTC)

    def test_microsecond_too_large(self):
        with pytest.raises(ValueError, match="microsecond must be in 0..999999"):
            UDT(2024, 1, 1, 0, 0, 0, 1_000_000, UTC)


# ============================================================
# UDT — String representations
# ============================================================


class TestUDTStr:
    def test_basic(self):
        u = UDT(2024, 6, 15, 10, 30, 45, tzinfo=UTC)
        assert str(u) == "2024-06-15 10:30:45 UTC"

    def test_with_microseconds(self):
        u = UDT(2024, 6, 15, 10, 30, 45, 123456, UTC)
        assert str(u) == "2024-06-15 10:30:45.123456 UTC"

    def test_negative_year(self):
        u = UDT(-50, 3, 15, tzinfo=UTC)
        assert str(u) == "-0050-03-15 00:00:00 UTC"

    def test_year_zero(self):
        u = UDT(0, 1, 1, tzinfo=UTC)
        assert str(u) == "0000-01-01 00:00:00 UTC"

    def test_with_offset(self):
        tz = Timezone(hours=5, minutes=30)
        u = UDT(2024, 6, 15, 10, 30, 0, 0, tz)
        assert str(u) == "2024-06-15 10:30:00 UTC+05:30"


class TestUDTRepr:
    def test_repr(self):
        u = UDT(2024, 6, 15, 10, 30, 45, 123456, UTC)
        assert repr(u) == "UDT(2024, 6, 15, 10, 30, 45, 123456, UTC)"


# ============================================================
# UDT — ISO 8601
# ============================================================


class TestUDTIsoformat:
    def test_basic(self):
        u = UDT(2024, 6, 15, 10, 30, 45, tzinfo=UTC)
        assert u.isoformat() == "2024-06-15T10:30:45+00:00"

    def test_with_microseconds(self):
        u = UDT(2024, 6, 15, 10, 30, 45, 123456, UTC)
        assert u.isoformat() == "2024-06-15T10:30:45.123456+00:00"

    def test_negative_year(self):
        u = UDT(-50, 3, 15, tzinfo=UTC)
        assert u.isoformat() == "-0050-03-15T00:00:00+00:00"

    def test_extended_year(self):
        u = UDT(10_000, 6, 15, 12, 0, 0, 0, UTC)
        assert u.isoformat() == "+10000-06-15T12:00:00+00:00"

    def test_with_positive_offset(self):
        tz = Timezone(hours=5, minutes=30)
        u = UDT(2024, 6, 15, 10, 30, 0, 0, tz)
        assert u.isoformat() == "2024-06-15T10:30:00+05:30"

    def test_with_negative_offset(self):
        tz = Timezone(hours=3, minutes=30, negative=True)
        u = UDT(2024, 6, 15, 10, 30, 0, 0, tz)
        assert u.isoformat() == "2024-06-15T10:30:00-03:30"


class TestUDTFromisoformat:
    def test_basic_with_t(self):
        u = UDT.fromisoformat("2024-06-15T10:30:45+05:00")
        assert u.year == 2024
        assert u.month == 6
        assert u.day == 15
        assert u.hour == 10
        assert u.minute == 30
        assert u.second == 45
        assert u.tzinfo == Timezone(hours=5)

    def test_with_space_separator(self):
        u = UDT.fromisoformat("2024-06-15 10:30:45+05:00")
        assert u.year == 2024
        assert u.hour == 10

    def test_date_only(self):
        u = UDT.fromisoformat("2024-06-15")
        assert u.year == 2024
        assert u.month == 6
        assert u.day == 15
        assert u.hour == 0
        assert u.minute == 0
        assert u.second == 0

    def test_utc_z(self):
        u = UDT.fromisoformat("2024-06-15T10:30:45Z")
        assert u.tzinfo == UTC

    def test_negative_year(self):
        u = UDT.fromisoformat("-0050-03-15T00:00:00Z")
        assert u.year == -50

    def test_year_zero(self):
        u = UDT.fromisoformat("0000-01-01T00:00:00Z")
        assert u.year == 0

    def test_extended_year(self):
        u = UDT.fromisoformat("+10000-06-15T12:00:00-03:30")
        assert u.year == 10_000
        assert u.tzinfo == Timezone(hours=3, minutes=30, negative=True)

    def test_with_microseconds(self):
        u = UDT.fromisoformat("2024-06-15T10:30:45.123456+00:00")
        assert u.microsecond == 123456

    def test_with_short_fraction(self):
        u = UDT.fromisoformat("2024-06-15T10:30:45.12+00:00")
        assert u.microsecond == 120000

    def test_negative_offset(self):
        u = UDT.fromisoformat("2024-06-15T10:30:45-05:00")
        assert u.tzinfo == Timezone(hours=5, negative=True)

    def test_offset_with_seconds(self):
        u = UDT.fromisoformat("2024-06-15T10:30:45+05:45:30")
        assert u.tzinfo == Timezone(hours=5, minutes=45, seconds=30)

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid ISO 8601 format"):
            UDT.fromisoformat("not-a-date")

    def test_roundtrip(self):
        tz = Timezone(hours=5, minutes=30)
        original = UDT(2024, 6, 15, 10, 30, 45, 123456, tz)
        restored = UDT.fromisoformat(original.isoformat())
        assert original == restored

    def test_roundtrip_negative_year(self):
        original = UDT(-1000, 6, 15, 12, 0, 0, 0, UTC)
        restored = UDT.fromisoformat(original.isoformat())
        assert original == restored

    def test_roundtrip_extended_year(self):
        original = UDT(100_000, 1, 1, 0, 0, 0, 0, UTC)
        restored = UDT.fromisoformat(original.isoformat())
        assert original == restored


# ============================================================
# UDT — Factory methods and conversions
# ============================================================


class TestUDTNow:
    def test_now_returns_udt(self):
        u = UDT.now()
        assert isinstance(u, UDT)
        assert u.year > 2000


class TestUDTTimestamp:
    def test_unix_epoch(self):
        u = UDT(1970, 1, 1, 0, 0, 0, 0, UTC)
        assert u.timestamp() == 0.0

    def test_positive_timestamp(self):
        u = UDT(2024, 1, 1, 0, 0, 0, 0, UTC)
        expected = datetime(2024, 1, 1, tzinfo=dt_timezone.utc).timestamp()
        assert u.timestamp() == expected

    def test_negative_timestamp(self):
        u = UDT(1969, 12, 31, 23, 59, 59, 0, UTC)
        assert u.timestamp() == -1.0

    def test_timestamp_with_offset(self):
        tz = Timezone(hours=5)
        u = UDT(1970, 1, 1, 5, 0, 0, 0, tz)
        assert u.timestamp() == 0.0


class TestUDTFromTimestamp:
    def test_unix_epoch(self):
        u = UDT.from_timestamp(0.0, UTC)
        assert u == UDT(1970, 1, 1, 0, 0, 0, 0, UTC)

    def test_positive(self):
        ts = 1_718_451_045.123456
        u = UDT.from_timestamp(ts, UTC)
        assert abs(u.timestamp() - ts) < 1e-6

    def test_negative(self):
        u = UDT.from_timestamp(-86400.0, UTC)
        assert u == UDT(1969, 12, 31, 0, 0, 0, 0, UTC)

    def test_with_offset(self):
        tz = Timezone(hours=5)
        u = UDT.from_timestamp(0.0, tz)
        assert u.hour == 5
        assert u.timestamp() == 0.0

    def test_roundtrip(self):
        original = UDT(2024, 6, 15, 10, 30, 45, 0, UTC)
        ts = original.timestamp()
        restored = UDT.from_timestamp(ts, UTC)
        assert original == restored

    def test_local_timezone_default(self):
        u = UDT.from_timestamp(0.0)
        assert isinstance(u, UDT)
        assert u.timestamp() == 0.0


class TestUDTDatetime:
    def test_from_datetime(self):
        dt = datetime(2024, 6, 15, 10, 30, 45, 123456, dt_timezone.utc)
        u = UDT.from_datetime(dt)
        assert u.year == 2024
        assert u.month == 6
        assert u.day == 15
        assert u.hour == 10
        assert u.minute == 30
        assert u.second == 45
        assert u.microsecond == 123456
        assert u.tzinfo == UTC

    def test_from_datetime_with_offset(self):
        tz = dt_timezone(timedelta(hours=5, minutes=30))
        dt = datetime(2024, 6, 15, 10, 30, 0, 0, tz)
        u = UDT.from_datetime(dt)
        assert u.tzinfo == Timezone(hours=5, minutes=30)

    def test_from_naive_datetime_raises(self):
        with pytest.raises(ValueError, match="naive datetime"):
            UDT.from_datetime(datetime(2024, 1, 1))

    def test_to_datetime(self):
        u = UDT(2024, 6, 15, 10, 30, 45, 123456, UTC)
        dt = u.to_datetime()
        assert dt.year == 2024
        assert dt.month == 6
        assert dt.day == 15
        assert dt.hour == 10
        assert dt.minute == 30
        assert dt.second == 45
        assert dt.microsecond == 123456

    def test_to_datetime_negative_year_raises(self):
        u = UDT(-50, 1, 1, tzinfo=UTC)
        with pytest.raises(ValueError):
            u.to_datetime()

    def test_roundtrip(self):
        dt = datetime(2024, 6, 15, 10, 30, 45, 123456, dt_timezone.utc)
        restored = UDT.from_datetime(dt).to_datetime()
        assert dt == restored


# ============================================================
# UDT — Timezone conversion
# ============================================================


class TestUDTAstimezone:
    def test_utc_to_offset(self):
        u = UDT(2024, 6, 15, 0, 0, 0, 0, UTC)
        tz5 = Timezone(hours=5)
        converted = u.astimezone(tz5)
        assert converted.hour == 5
        assert converted.day == 15
        assert converted.tzinfo == tz5

    def test_same_instant(self):
        tz5 = Timezone(hours=5)
        u = UDT(2024, 6, 15, 10, 0, 0, 0, tz5)
        u_utc = u.astimezone(UTC)
        assert u == u_utc

    def test_day_rollover_forward(self):
        u = UDT(2024, 6, 15, 23, 0, 0, 0, UTC)
        tz5 = Timezone(hours=5)
        converted = u.astimezone(tz5)
        assert converted.day == 16
        assert converted.hour == 4

    def test_day_rollover_backward(self):
        u = UDT(2024, 6, 15, 2, 0, 0, 0, UTC)
        tz_minus5 = Timezone(hours=5, negative=True)
        converted = u.astimezone(tz_minus5)
        assert converted.day == 14
        assert converted.hour == 21

    def test_preserves_microseconds(self):
        u = UDT(2024, 6, 15, 10, 30, 45, 123456, UTC)
        tz3 = Timezone(hours=3)
        converted = u.astimezone(tz3)
        assert converted.microsecond == 123456


# ============================================================
# UDT — Replace
# ============================================================


class TestUDTReplace:
    def test_replace_year(self):
        u = UDT(2024, 6, 15, tzinfo=UTC)
        assert u.replace(year=2025).year == 2025

    def test_replace_month(self):
        u = UDT(2024, 6, 15, tzinfo=UTC)
        assert u.replace(month=3).month == 3

    def test_replace_day(self):
        u = UDT(2024, 6, 15, tzinfo=UTC)
        assert u.replace(day=20).day == 20

    def test_replace_hour(self):
        u = UDT(2024, 6, 15, 10, tzinfo=UTC)
        assert u.replace(hour=15).hour == 15

    def test_replace_minute(self):
        u = UDT(2024, 6, 15, 10, 30, tzinfo=UTC)
        assert u.replace(minute=45).minute == 45

    def test_replace_second(self):
        u = UDT(2024, 6, 15, 10, 30, 45, tzinfo=UTC)
        assert u.replace(second=0).second == 0

    def test_replace_microsecond(self):
        u = UDT(2024, 6, 15, 10, 30, 45, 123456, UTC)
        assert u.replace(microsecond=0).microsecond == 0

    def test_replace_tzinfo(self):
        u = UDT(2024, 6, 15, tzinfo=UTC)
        tz5 = Timezone(hours=5)
        assert u.replace(tzinfo=tz5).tzinfo == tz5

    def test_replace_preserves_other_fields(self):
        u = UDT(2024, 6, 15, 10, 30, 45, 123456, UTC)
        replaced = u.replace(year=2025)
        assert replaced.month == 6
        assert replaced.day == 15
        assert replaced.hour == 10
        assert replaced.minute == 30
        assert replaced.second == 45
        assert replaced.microsecond == 123456
        assert replaced.tzinfo == UTC


# ============================================================
# UDT — Date utilities
# ============================================================


class TestUDTDate:
    def test_date_tuple(self):
        u = UDT(2024, 6, 15, tzinfo=UTC)
        assert u.date() == (2024, 6, 15)

    def test_date_negative_year(self):
        u = UDT(-50, 3, 15, tzinfo=UTC)
        assert u.date() == (-50, 3, 15)


class TestUDTWeekday:
    def test_known_monday(self):
        # 2024-01-01 is a Monday
        assert UDT(2024, 1, 1, tzinfo=UTC).weekday() == 0

    def test_known_friday(self):
        # 2024-06-14 is a Friday
        assert UDT(2024, 6, 14, tzinfo=UTC).weekday() == 4

    def test_known_sunday(self):
        # 2024-06-16 is a Sunday
        assert UDT(2024, 6, 16, tzinfo=UTC).weekday() == 6

    def test_negative_year(self):
        # Verify weekday works for negative years (just that it returns 0-6)
        w = UDT(-1000, 1, 1, tzinfo=UTC).weekday()
        assert 0 <= w <= 6


class TestUDTYearday:
    def test_jan_1(self):
        assert UDT(2024, 1, 1, tzinfo=UTC).yearday() == 1

    def test_feb_1(self):
        assert UDT(2024, 2, 1, tzinfo=UTC).yearday() == 32

    def test_dec_31_leap(self):
        assert UDT(2024, 12, 31, tzinfo=UTC).yearday() == 366

    def test_dec_31_non_leap(self):
        assert UDT(2023, 12, 31, tzinfo=UTC).yearday() == 365

    def test_mar_1_leap(self):
        # Jan (31) + Feb (29) + 1 = 61
        assert UDT(2024, 3, 1, tzinfo=UTC).yearday() == 61

    def test_mar_1_non_leap(self):
        # Jan (31) + Feb (28) + 1 = 60
        assert UDT(2023, 3, 1, tzinfo=UTC).yearday() == 60


class TestUDTDaysinmonth:
    def test_january(self):
        assert UDT(2024, 1, 1, tzinfo=UTC).daysinmonth() == 31

    def test_february_leap(self):
        assert UDT(2024, 2, 1, tzinfo=UTC).daysinmonth() == 29

    def test_february_non_leap(self):
        assert UDT(2023, 2, 1, tzinfo=UTC).daysinmonth() == 28

    def test_february_century_non_leap(self):
        assert UDT(1900, 2, 1, tzinfo=UTC).daysinmonth() == 28

    def test_february_400_year_leap(self):
        assert UDT(2000, 2, 1, tzinfo=UTC).daysinmonth() == 29

    def test_april(self):
        assert UDT(2024, 4, 1, tzinfo=UTC).daysinmonth() == 30

    def test_negative_year_leap(self):
        assert UDT(-400, 2, 1, tzinfo=UTC).daysinmonth() == 29


# ============================================================
# UDT — Comparison and hashing
# ============================================================


class TestUDTComparison:
    def test_equal_same_tz(self):
        a = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        b = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        assert a == b

    def test_equal_different_tz(self):
        """Same instant expressed in different timezones must be equal."""
        tz5 = Timezone(hours=5)
        a = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        b = UDT(2024, 6, 15, 15, 0, 0, 0, tz5)
        assert a == b

    def test_not_equal(self):
        a = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        b = UDT(2024, 6, 15, 11, 0, 0, 0, UTC)
        assert a != b

    def test_lt(self):
        a = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        b = UDT(2024, 6, 15, 11, 0, 0, 0, UTC)
        assert a < b

    def test_le(self):
        a = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        assert a <= a
        assert a <= UDT(2024, 6, 15, 11, 0, 0, 0, UTC)

    def test_gt(self):
        a = UDT(2024, 6, 15, 11, 0, 0, 0, UTC)
        b = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        assert a > b

    def test_ge(self):
        a = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        assert a >= a
        assert UDT(2024, 6, 15, 11, 0, 0, 0, UTC) >= a

    def test_lt_cross_timezone(self):
        """Earlier instant in a higher offset is still earlier."""
        tz5 = Timezone(hours=5)
        a = UDT(2024, 6, 15, 14, 0, 0, 0, tz5)  # 09:00 UTC
        b = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)  # 10:00 UTC
        assert a < b

    def test_not_equal_to_other_type(self):
        assert UDT(2024, 1, 1, tzinfo=UTC) != 42

    def test_ordering_with_other_type_raises(self):
        u = UDT(2024, 1, 1, tzinfo=UTC)
        with pytest.raises(TypeError):
            u < 42  # type: ignore[operator]
        with pytest.raises(TypeError):
            u > 42  # type: ignore[operator]
        with pytest.raises(TypeError):
            u <= 42  # type: ignore[operator]
        with pytest.raises(TypeError):
            u >= 42  # type: ignore[operator]


class TestUDTHash:
    def test_equal_objects_same_hash(self):
        a = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        b = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        assert hash(a) == hash(b)

    def test_equal_different_tz_same_hash(self):
        tz5 = Timezone(hours=5)
        a = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        b = UDT(2024, 6, 15, 15, 0, 0, 0, tz5)
        assert hash(a) == hash(b)

    def test_usable_in_set(self):
        tz5 = Timezone(hours=5)
        a = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        b = UDT(2024, 6, 15, 15, 0, 0, 0, tz5)
        c = UDT(2024, 6, 15, 11, 0, 0, 0, UTC)
        assert len({a, b, c}) == 2


# ============================================================
# UDT — Arithmetic
# ============================================================


class TestUDTArithmetic:
    def test_add_timedelta(self):
        u = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        td = Timedelta(hours=3)
        result = u + td
        assert result.hour == 13
        assert result.day == 15

    def test_add_crosses_day(self):
        u = UDT(2024, 6, 15, 23, 0, 0, 0, UTC)
        td = Timedelta(hours=2)
        result = u + td
        assert result.day == 16
        assert result.hour == 1

    def test_add_crosses_month(self):
        u = UDT(2024, 6, 30, 23, 0, 0, 0, UTC)
        td = Timedelta(hours=2)
        result = u + td
        assert result.month == 7
        assert result.day == 1

    def test_add_negative_timedelta(self):
        u = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        td = Timedelta(hours=3, negative=True)
        result = u + td
        assert result.hour == 7

    def test_radd(self):
        u = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        td = Timedelta(hours=3)
        result = td + u
        assert result == u + td

    def test_sub_timedelta(self):
        u = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        td = Timedelta(hours=3)
        result = u - td
        assert result.hour == 7

    def test_sub_udt(self):
        a = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        b = UDT(2024, 6, 15, 7, 0, 0, 0, UTC)
        result = a - b
        assert isinstance(result, Timedelta)
        assert result.microseconds == 3 * 3_600_000_000

    def test_sub_udt_negative_result(self):
        a = UDT(2024, 6, 15, 7, 0, 0, 0, UTC)
        b = UDT(2024, 6, 15, 10, 0, 0, 0, UTC)
        result = a - b
        assert result.microseconds < 0

    def test_sub_udt_cross_timezone(self):
        tz5 = Timezone(hours=5)
        a = UDT(2024, 6, 15, 15, 0, 0, 0, tz5)  # 10:00 UTC
        b = UDT(2024, 6, 15, 7, 0, 0, 0, UTC)  # 07:00 UTC
        result = a - b
        assert result.microseconds == 3 * 3_600_000_000

    def test_add_preserves_timezone(self):
        tz5 = Timezone(hours=5)
        u = UDT(2024, 6, 15, 10, 0, 0, 0, tz5)
        result = u + Timedelta(hours=1)
        assert result.tzinfo == tz5

    def test_add_with_other_type_raises(self):
        with pytest.raises(TypeError):
            UDT(2024, 1, 1, tzinfo=UTC) + 42  # type: ignore[operator]

    def test_sub_with_other_type_raises(self):
        with pytest.raises(TypeError):
            UDT(2024, 1, 1, tzinfo=UTC) - 42  # type: ignore[operator]


# ============================================================
# UDT — Pickle
# ============================================================


class TestUDTPickle:
    def test_roundtrip(self):
        tz = Timezone(hours=5, minutes=30)
        u = UDT(2024, 6, 15, 10, 30, 45, 123456, tz)
        restored = pickle.loads(pickle.dumps(u))
        assert u == restored
        assert restored.year == 2024
        assert restored.microsecond == 123456
        assert restored.tzinfo == tz

    def test_negative_year(self):
        u = UDT(-1000, 6, 15, tzinfo=UTC)
        restored = pickle.loads(pickle.dumps(u))
        assert u == restored
        assert restored.year == -1000

    def test_preserves_str(self):
        u = UDT(2024, 6, 15, 10, 30, 45, 123456, UTC)
        restored = pickle.loads(pickle.dumps(u))
        assert str(u) == str(restored)


# ============================================================
# UDT — Core design: exact integer arithmetic
# ============================================================


class TestUDTExactArithmetic:
    def test_no_rounding_microsecond_add_sub(self):
        """Adding then subtracting 1 microsecond must be exact."""
        u = UDT(2024, 6, 15, 12, 0, 0, 0, UTC)
        one_us = Timedelta(microseconds=1)
        assert u + one_us - one_us == u

    def test_no_drift_many_additions(self):
        """86400 additions of 1 second must equal exactly 1 day."""
        u = UDT(2024, 6, 15, 0, 0, 0, 0, UTC)
        one_sec = Timedelta(seconds=1)
        result = u
        for _ in range(86400):
            result = result + one_sec
        expected = UDT(2024, 6, 16, 0, 0, 0, 0, UTC)
        assert result == expected

    def test_large_timedelta_exact(self):
        """Adding/subtracting 1000 days must be exact."""
        u = UDT(2024, 6, 15, 12, 30, 45, 999999, UTC)
        td = Timedelta(days=1000)
        assert u + td - td == u

    def test_cross_timezone_equality_exact(self):
        """Same instant in UTC+5 and UTC must be exactly equal."""
        tz5 = Timezone(hours=5)
        a = UDT(2024, 6, 15, 5, 0, 0, 0, tz5)
        b = UDT(2024, 6, 15, 0, 0, 0, 0, UTC)
        assert a == b
        assert a.timestamp() == b.timestamp()

    def test_timestamp_roundtrip_exact(self):
        """timestamp() -> from_timestamp() must be exact for integer seconds."""
        u = UDT(2024, 6, 15, 12, 30, 45, 0, UTC)
        assert UDT.from_timestamp(u.timestamp(), UTC) == u
