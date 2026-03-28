import math


class BitSize:
    BITS = 1
    KILO_BITS = 1000
    MEGA_BITS = KILO_BITS * 1000
    GIGA_BITS = MEGA_BITS * 1000
    TERA_BITS = GIGA_BITS * 1000
    BASES = [BITS, KILO_BITS, MEGA_BITS, GIGA_BITS, TERA_BITS]
    NAMES = ["b", "kb", "Mb", "Gb", "Tb"]

    __slots__ = ("__raw", "__neg", "__size", "__base")

    def __init__(self, size: int):
        raw = size
        neg = size < 0
        size = abs(size)
        self.__raw = raw
        self.__neg = neg
        self.__size = size
        self.__base = (size and min(4, int(math.log(size, 1000)))) or 0

    def __hash__(self):
        return hash(self.__raw)

    def __int__(self):
        return int(self.__raw)

    def __float__(self):
        return float(self.__raw)

    def __eq__(self, other):
        return isinstance(other, BitSize) and self.__raw == other.__raw

    def __ne__(self, other):
        if not isinstance(other, BitSize):
            return NotImplemented
        return self.__raw != other.__raw

    def __lt__(self, other):
        if not isinstance(other, BitSize):
            return NotImplemented
        return self.__raw < other.__raw

    def __gt__(self, other):
        if not isinstance(other, BitSize):
            return NotImplemented
        return self.__raw > other.__raw

    def __le__(self, other):
        if not isinstance(other, BitSize):
            return NotImplemented
        return self.__raw <= other.__raw

    def __ge__(self, other):
        if not isinstance(other, BitSize):
            return NotImplemented
        return self.__raw >= other.__raw

    def __str__(self):
        return (
            f"{'-' if self.__neg else ''}"
            f"{round(self.__size / self.BASES[self.__base], 2) if self.__size else 0} "
            f"{self.NAMES[self.__base]}"
        )
