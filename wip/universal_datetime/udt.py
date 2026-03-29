from __future__ import annotations

import re
from datetime import datetime, timedelta, tzinfo as _python_tzinfo
from typing import Self, overload

S_TO_US = 1_000_000
M_TO_US = 60 * S_TO_US
H_TO_US = 60 * M_TO_US
D_TO_US = 24 * H_TO_US


class Microseconds:
    __slots__ = ("_microseconds",)

    def __init__(
        self,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        microseconds: int = 0,
        negative: bool = False,
    ):
        if days < 0:
            raise ValueError(f"days must be >= 0, got {days}")
        if hours < 0:
            raise ValueError(f"hours must be >= 0, got {hours}")
        if minutes < 0:
            raise ValueError(f"minutes must be >= 0, got {minutes}")
        if seconds < 0:
            raise ValueError(f"seconds must be >= 0, got {seconds}")
        if microseconds < 0:
            raise ValueError(f"microseconds must be >= 0, got {microseconds}")
        self._microseconds = (
            microseconds
            + seconds * S_TO_US
            + minutes * M_TO_US
            + hours * H_TO_US
            + days * D_TO_US
        ) * (-1 if negative else 1)

    def __neg__(self) -> Self:
        return type(self)(
            microseconds=abs(self._microseconds), negative=(self._microseconds > 0)
        )

    def __hash__(self):
        return hash(self._microseconds)

    def __eq__(self, other):
        if type(self) is not type(other):
            return NotImplemented
        return self._microseconds == other._microseconds

    def __lt__(self, other):
        if type(self) is not type(other):
            return NotImplemented
        return self._microseconds < other._microseconds

    def __gt__(self, other):
        if type(self) is not type(other):
            return NotImplemented
        return self._microseconds > other._microseconds

    def __le__(self, other):
        if type(self) is not type(other):
            return NotImplemented
        return self._microseconds <= other._microseconds

    def __ge__(self, other):
        if type(self) is not type(other):
            return NotImplemented
        return self._microseconds >= other._microseconds

    @property
    def microseconds(self) -> int:
        return self._microseconds


class ArithmeticMicroseconds(Microseconds):
    __slots__ = ()

    def __add__(self, other: Self) -> Self:
        if type(self) is not type(other):
            return NotImplemented
        total = self._microseconds + other._microseconds
        return type(self)(microseconds=abs(total), negative=(total < 0))

    def __sub__(self, other: Self) -> Self:
        if type(self) is not type(other):
            return NotImplemented
        total = self._microseconds - other._microseconds
        return type(self)(microseconds=abs(total), negative=(total < 0))


class Timezone(_python_tzinfo, Microseconds):
    """Timezone, stored as signed microseconds."""

    __slots__ = ()

    def _format_offset(self) -> tuple[str, int, int, int]:
        sign = "+" if self._microseconds >= 0 else "-"
        total_seconds = abs(self._microseconds) // S_TO_US
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return sign, hours, minutes, seconds

    def tzname(self, dt, /):
        if self._microseconds == 0:
            return "UTC"
        sign, hours, minutes, seconds = self._format_offset()
        if seconds:
            return f"UTC{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"UTC{sign}{hours:02d}:{minutes:02d}"

    def utcoffset(self, dt, /):
        return timedelta(microseconds=self._microseconds)

    def dst(self, dt, /):
        return timedelta(0)

    def isoformat(self) -> str:
        sign, hours, minutes, seconds = self._format_offset()
        if seconds:
            return f"{sign}{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{sign}{hours:02d}:{minutes:02d}"

    def __hash__(self):
        return Microseconds.__hash__(self)

    def __eq__(self, other):
        return Microseconds.__eq__(self, other)

    def __repr__(self):
        return self.tzname(None)


class Timedelta(ArithmeticMicroseconds):
    """Duration, stored as signed microseconds."""

    __slots__ = ()

    def __str__(self):
        """String representation of the timedelta. Omits zero units."""
        sign = "-" if self._microseconds < 0 else ""
        total = abs(self._microseconds)
        d = total // D_TO_US
        h = total % D_TO_US // H_TO_US
        m = total % H_TO_US // M_TO_US
        s = total % M_TO_US // S_TO_US
        u = total % S_TO_US
        parts = (
            (f"{d:02d}d" if d else "")
            + (f" {h:02d}h" if h else "")
            + (f" {m:02d}m" if m else "")
            + (f" {s:02d}s" if s else "")
            + (f" {u:06d}us" if u else "")
        ).strip()
        return sign + (parts or "00s")

    @property
    def short(self) -> str:
        sign = "-" if self._microseconds < 0 else ""
        us = abs(self._microseconds)
        d, remainder = divmod(us, D_TO_US)
        h, remainder = divmod(remainder, H_TO_US)
        m, remainder = divmod(remainder, M_TO_US)
        s, lasting_us = divmod(remainder, S_TO_US)
        view = []
        if d:
            view.append(f"{d:02d}d")
        view.append(f"{h:02d}")
        view.append(f"{m:02d}")
        view.append(f"{s:02d}")
        if lasting_us:
            view.append(f"{lasting_us:06d}")
        return sign + ":".join(view)

    @classmethod
    def from_timedelta(cls, td: timedelta) -> Timedelta:
        total_us = _timedelta_to_microseconds(td)
        return cls(microseconds=abs(total_us), negative=(total_us < 0))

    def to_timedelta(self) -> timedelta:
        return timedelta(microseconds=self._microseconds)

    def __repr__(self):
        return f"Timedelta({self})"


_DAYS_IN_MONTH = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _is_leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _days_in_month(year: int, month: int) -> int:
    if month == 2 and _is_leap_year(year):
        return 29
    return _DAYS_IN_MONTH[month]


def _date_to_jdn(year: int, month: int, day: int) -> int:
    """Convert a proleptic Gregorian date to Julian Day Number.

    JDN is a continuous day count since January 1, 4713 BC (astronomical convention),
    making date arithmetic trivial (add/subtract days).
    Uses the Richards algorithm (Meeus, Astronomical Algorithms).
    """
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def _jdn_to_date(jdn: int) -> tuple[int, int, int]:
    """Convert a Julian Day Number back to a proleptic Gregorian date.

    Inverse of _date_to_jdn. Uses the Richards algorithm (Meeus, Astronomical Algorithms).
    """
    a = jdn + 32044
    b = (4 * a + 3) // 146097
    c = a - (146097 * b) // 4
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = 100 * b + d - 4800 + m // 10
    return year, month, day


_UNIX_EPOCH_JDN = _date_to_jdn(1970, 1, 1)


def _timedelta_to_microseconds(t: timedelta) -> int:
    return t.days * D_TO_US + t.seconds * S_TO_US + t.microseconds


def _local_timezone():
    """
    Dynamically infer local timezone.

    Allow to get local timezone at runtime,
    e.g. if time zone changes during code execution.

    But, it seems to make a system call each time.
    Is it performance-consuming ?
    """
    offset = datetime.now().astimezone().utcoffset()
    if offset is None:
        raise RuntimeError("datetime.now().astimezone().utcoffset() is None")
    total_us = _timedelta_to_microseconds(offset)
    return Timezone(microseconds=abs(total_us), negative=(total_us < 0))


_ISO_RE = re.compile(
    r"^(?P<year>[+-]?\d{4,})-(?P<month>\d{2})-(?P<day>\d{2})"
    r"(?:[T ](?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
    r"(?:\.(?P<frac>\d+))?)?"
    r"(?P<tz>Z|[+-]\d{2}:\d{2}(?::\d{2})?)?$"
)


class UDT:
    """Universal datetime in Proleptic Gregorian calendar, supporting negative years"""

    __slots__ = (
        "__y",
        "__m",
        "__d",
        "__h",
        "__i",
        "__s",
        "__u",
        "__z",
        "__jdn",
        "__utc",
    )

    def __init__(
        self,
        year: int,
        month: int = 1,
        day: int = 1,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        microsecond: int = 0,
        tzinfo: Timezone | None = None,
    ):
        if not 1 <= month <= 12:
            raise ValueError(f"month must be in 1..12, got {month}")
        if not 1 <= day <= _days_in_month(year, month):
            raise ValueError(
                f"day must be in 1..{_days_in_month(year, month)}"
                f" for {year}-{month:02d}, got {day}"
            )
        if not 0 <= hour < 24:
            raise ValueError(f"hour must be in 0..23, got {hour}")
        if not 0 <= minute < 60:
            raise ValueError(f"minute must be in 0..59, got {minute}")
        if not 0 <= second < 60:
            raise ValueError(f"second must be in 0..59, got {second}")
        if not 0 <= microsecond < S_TO_US:
            raise ValueError(
                f"microsecond must be in 0..{S_TO_US - 1}, got {microsecond}"
            )
        self.__y = year
        self.__m = month
        self.__d = day
        self.__h = hour
        self.__i = minute
        self.__s = second
        self.__u = microsecond
        self.__z = _local_timezone() if tzinfo is None else tzinfo
        self.__jdn = _date_to_jdn(year, month, day)
        us = hour * H_TO_US + minute * M_TO_US + second * S_TO_US + microsecond
        us -= self.__z.microseconds
        extra_days, us = divmod(us, D_TO_US)
        self.__utc = (self.__jdn + extra_days, us)

    @property
    def year(self) -> int:
        return self.__y

    @property
    def month(self) -> int:
        return self.__m

    @property
    def day(self) -> int:
        return self.__d

    @property
    def hour(self) -> int:
        return self.__h

    @property
    def minute(self) -> int:
        return self.__i

    @property
    def second(self) -> int:
        return self.__s

    @property
    def microsecond(self) -> int:
        return self.__u

    @property
    def tzinfo(self) -> Timezone:
        return self.__z

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}"
            f"({self.__y}, {self.__m}, {self.__d}, {self.__h}, {self.__i}, {self.__s}, {self.__u}, {self.__z})"
        )

    def __str__(self):
        sign = "-" if self.__y < 0 else ""
        us = f".{self.__u:06d}" if self.__u else ""
        return (
            f"{sign}{abs(self.__y):04d}-{self.__m:02d}-{self.__d:02d}"
            f" {self.__h:02d}:{self.__i:02d}:{self.__s:02d}"
            f"{us} {self.__z.tzname(None)}"
        )

    def isoformat(self) -> str:
        ay = abs(self.__y)
        sign = "-" if self.__y < 0 else ("+" if ay > 9999 else "")
        us = f".{self.__u:06d}" if self.__u else ""
        return (
            f"{sign}{ay:04d}-{self.__m:02d}-{self.__d:02d}"
            f"T{self.__h:02d}:{self.__i:02d}:{self.__s:02d}"
            f"{us}{self.__z.isoformat()}"
        )

    @classmethod
    def fromisoformat(cls, s: str) -> UDT:
        """Parse an ISO 8601 datetime string.

        Supports negative/extended years, 'T' or space separator, 'Z' for UTC,
        and optional microseconds. Examples:
            2000-06-15T12:30:45.123456+05:00
            -0050-03-15T00:00:00Z
            0000-01-01
            +10000-06-15T12:00:00-03:30
        """
        m = _ISO_RE.match(s)
        if not m:
            raise ValueError(f"Invalid ISO 8601 format: {s!r}")
        year = int(m.group("year"))
        month = int(m.group("month"))
        day = int(m.group("day"))
        hour = int(m.group("hour") or 0)
        minute = int(m.group("minute") or 0)
        second = int(m.group("second") or 0)
        us_str = m.group("frac") or ""
        microsecond = int(us_str.ljust(6, "0")[:6]) if us_str else 0
        tz_str = m.group("tz")
        if tz_str is None:
            tz = _local_timezone()
        elif tz_str == "Z":
            tz = Timezone()
        else:
            tz_sign = tz_str[0] == "-"
            tz_h = int(tz_str[1:3])
            tz_m = int(tz_str[4:6])
            tz_s = int(tz_str[7:9]) if len(tz_str) > 6 else 0
            tz = Timezone(hours=tz_h, minutes=tz_m, seconds=tz_s, negative=tz_sign)
        return cls(year, month, day, hour, minute, second, microsecond, tz)

    @classmethod
    def now(cls) -> UDT:
        return cls.from_datetime(datetime.now().astimezone())

    @classmethod
    def from_timestamp(cls, ts: float, tz: Timezone | None = None) -> UDT:
        """Inverse of timestamp(). Converts seconds since Unix epoch to UDT.

        If tz is None, uses local timezone.
        """
        if tz is None:
            tz = _local_timezone()
        # Reverse of: (jdn - _UNIX_EPOCH_JDN) * 86400 + us / S_TO_US
        total_us = round(ts * S_TO_US)
        utc_days, utc_us = divmod(total_us, D_TO_US)
        jdn = _UNIX_EPOCH_JDN + utc_days
        # Convert from UTC to local time by adding timezone offset
        local_us = utc_us + tz.microseconds
        extra_days, local_us = divmod(local_us, D_TO_US)
        jdn += extra_days
        year, month, day = _jdn_to_date(jdn)
        return cls(
            year,
            month,
            day,
            local_us // H_TO_US,
            local_us % H_TO_US // M_TO_US,
            local_us % M_TO_US // S_TO_US,
            local_us % S_TO_US,
            tz,
        )

    @classmethod
    def from_datetime(cls, dt: datetime) -> UDT:
        """Convert a datetime to UDT. The datetime must be timezone-aware."""
        offset = dt.utcoffset()
        if offset is None:
            raise ValueError("Cannot convert naive datetime to UDT (no timezone info)")
        total_us = _timedelta_to_microseconds(offset)
        tz = Timezone(microseconds=abs(total_us), negative=(total_us < 0))
        return cls(
            dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond, tz
        )

    def to_datetime(self) -> datetime:
        """
        Convert to datetime. datetime will raise an exception if it cannot handle the year.

        We don't catch any error here to make the code forward-compatible,
        in case datetime evolves to support a wider year range.
        """
        return datetime(
            self.__y,
            self.__m,
            self.__d,
            self.__h,
            self.__i,
            self.__s,
            self.__u,
            self.__z,
        )

    def astimezone(self, tz: Timezone) -> UDT:
        """Convert to the same instant in a different timezone."""
        jdn, utc_us = self.__utc
        local_us = utc_us + tz.microseconds
        extra_days, local_us = divmod(local_us, D_TO_US)
        jdn += extra_days
        year, month, day = _jdn_to_date(jdn)
        return UDT(
            year,
            month,
            day,
            local_us // H_TO_US,
            local_us % H_TO_US // M_TO_US,
            local_us % M_TO_US // S_TO_US,
            local_us % S_TO_US,
            tz,
        )

    def replace(
        self,
        year: int | None = None,
        month: int | None = None,
        day: int | None = None,
        hour: int | None = None,
        minute: int | None = None,
        second: int | None = None,
        microsecond: int | None = None,
        tzinfo: Timezone | None = None,
    ) -> UDT:
        """Return a new UDT with specified fields replaced."""
        return UDT(
            self.__y if year is None else year,
            self.__m if month is None else month,
            self.__d if day is None else day,
            self.__h if hour is None else hour,
            self.__i if minute is None else minute,
            self.__s if second is None else second,
            self.__u if microsecond is None else microsecond,
            self.__z if tzinfo is None else tzinfo,
        )

    def date(self) -> tuple[int, int, int]:
        """Return (year, month, day) tuple."""
        return self.__y, self.__m, self.__d

    def weekday(self) -> int:
        """Day of the week: 0=Monday, 1=Tuesday, ..., 6=Sunday."""
        return self.__jdn % 7

    def __hash__(self):
        return hash(self.__utc)

    def __eq__(self, other):
        if not isinstance(other, UDT):
            return NotImplemented
        return self.__utc == other.__utc

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, UDT):
            return NotImplemented
        return self.__utc < other.__utc

    def __le__(self, other: object) -> bool:
        if not isinstance(other, UDT):
            return NotImplemented
        return self.__utc <= other.__utc

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, UDT):
            return NotImplemented
        return self.__utc > other.__utc

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, UDT):
            return NotImplemented
        return self.__utc >= other.__utc

    def timestamp(self) -> float:
        """Seconds since Unix epoch (1970-01-01 00:00:00 UTC). Negative for earlier dates."""
        jdn, us = self.__utc
        return (jdn - _UNIX_EPOCH_JDN) * 86400 + us / S_TO_US

    def __add__(self, other: Timedelta) -> UDT:
        if not isinstance(other, Timedelta):
            return NotImplemented
        jdn = self.__jdn
        us = self.__h * H_TO_US + self.__i * M_TO_US + self.__s * S_TO_US + self.__u
        total_us = us + other.microseconds
        extra_days, us = divmod(total_us, D_TO_US)
        jdn += extra_days
        year, month, day = _jdn_to_date(jdn)
        return UDT(
            year,
            month,
            day,
            us // H_TO_US,
            us % H_TO_US // M_TO_US,
            us % M_TO_US // S_TO_US,
            us % S_TO_US,
            self.__z,
        )

    def __radd__(self, other: Timedelta) -> UDT:
        return self.__add__(other)

    @overload
    def __sub__(self, other: Timedelta) -> UDT: ...
    @overload
    def __sub__(self, other: UDT) -> Timedelta: ...
    def __sub__(self, other: object) -> UDT | Timedelta:
        if isinstance(other, Timedelta):
            return self + (-other)
        if isinstance(other, UDT):
            jdn1, us1 = self.__utc
            jdn2, us2 = other.__utc
            total = (jdn1 - jdn2) * D_TO_US + (us1 - us2)
            return Timedelta(microseconds=abs(total), negative=(total < 0))
        return NotImplemented
