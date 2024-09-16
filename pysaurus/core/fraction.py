from pysaurus.core.functions import pgcd


class Fraction:
    __slots__ = "sign", "num", "den"

    def __init__(self, a, b=1):
        # type: (int, int) -> None
        if b == 0:
            raise ZeroDivisionError()
        if a == 0:
            self.sign = 1
            self.num = 0
            self.den = 1
            return
        if a < 0 and b < 0:
            self.sign = 1
            self.num = -a
            self.den = -b
        elif a > 0 and b > 0:
            self.sign = 1
            self.num = a
            self.den = b
        else:
            # a < 0 and b > 0, or a > 0 and b < 0
            self.sign = -1
            self.num = abs(a)
            self.den = abs(b)
        d = pgcd(self.num, self.den)
        self.num //= d
        self.den //= d

    def __float__(self):
        return self.sign * self.num / self.den

    def __str__(self):
        if self.den == 0:
            return "0"
        sign = "-" if self.sign < 0 else ""
        if self.den == 1:
            return f"{sign}{self.num}"
        return f"{sign}{self.num}/{self.den}"

    def __hash__(self):
        return hash((self.sign, self.num, self.den))

    def __eq__(self, other):
        return (
            self.sign == other.sign and self.num == other.num and self.den == other.den
        )

    def __lt__(self, other):
        if self.sign == other.sign:
            return self.sign * (self.num * other.den - self.den * other.num) < 0
        return self.sign < other.sign

    def __add__(self, other):
        return Fraction(
            self.sign * self.num * other.den + other.sign * other.num * self.den,
            self.den * other.den,
        )

    def __sub__(self, other):
        return Fraction(
            self.sign * self.num * other.den - other.sign * other.num * self.den,
            self.den * other.den,
        )

    def __mul__(self, other):
        return Fraction(
            self.sign * self.num * other.sign * other.num, self.den * other.den
        )

    def __truediv__(self, other):
        return Fraction(
            self.sign * self.num * other.den, self.den * other.sign * other.num
        )

    def __pow__(self, power: int):
        if power == 0:
            return Fraction(1)
        if power == 1:
            return self
        if power < 0:
            return Fraction(self.den**-power, self.sign * self.num**-power)
        return Fraction(self.sign * self.num**power, self.den**power)
