from datetime import timedelta


class Duration:
    __slots__ = ("d", "h", "m", "s", "u", "t", "sign")
    S = 1_000_000
    M = 60_000_000
    H = 3600_000_000
    D = 86_400_000_000

    def __init__(self, microseconds: int | float):
        # Extract sign
        self.sign = -1 if microseconds < 0 else 1
        # Round absolute value of microseconds to an integer
        microseconds = round(abs(microseconds))
        # Use rounded value to compute detailed duration parts
        self.d = microseconds // 86_400_000_000
        self.h = (microseconds % 86_400_000_000) // 3600_000_000
        self.m = (microseconds % 3600_000_000) // 60_000_000
        self.s = (microseconds % 60_000_000) // 1_000_000
        self.u = microseconds % 1_000_000

        # Keep rounded microseconds and original sign for hash and comparisons.
        self.t = self.sign * microseconds

    def __hash__(self):
        return hash(self.t)

    def __eq__(self, other):
        return self.t == other.t

    def __ne__(self, other):
        return self.t != other.t

    def __lt__(self, other):
        return self.t < other.t

    def __gt__(self, other):
        return self.t > other.t

    def __le__(self, other):
        return self.t <= other.t

    def __ge__(self, other):
        return self.t >= other.t

    def __str__(self):
        return ("-" if self.sign < 0 else "") + (
            (
                (f" {self.d:02d}d" if self.d else "")
                + (f" {self.h:02d}h" if self.h else "")
                + (f" {self.m:02d}m" if self.m else "")
                + (f" {self.s:02d}s" if self.s else "")
                + (f" {self.u:06d}µs" if self.u else "")
            )[1:]
            if self.t
            else "00s"
        )

    @classmethod
    def from_seconds(cls, seconds: int | float):
        return cls(seconds * 1_000_000)

    @classmethod
    def from_minutes(cls, minutes: int | float):
        return cls(minutes * 60_000_000)

    @classmethod
    def from_timedelta(cls, delta: timedelta):
        return cls.from_seconds(delta.total_seconds())


class ShortDuration(Duration):
    __slots__ = ()

    def __str__(self):
        seconds = round((self.s * 1000000 + self.u) / 1000000)
        view = []
        if self.d:
            view.append(f"{self.d:02d}d")
        view.append(f"{self.h:02d}")
        view.append(f"{self.m:02d}")
        view.append(f"{seconds:02d}")
        return ("-" if self.sign < 0 else "") + ":".join(view)
