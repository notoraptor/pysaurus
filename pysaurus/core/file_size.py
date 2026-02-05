import math


class FileSize:
    BYTES = 1
    KILO_BYTES = 1024
    MEGA_BYTES = KILO_BYTES * KILO_BYTES
    GIGA_BYTES = KILO_BYTES * MEGA_BYTES
    TERA_BYTES = KILO_BYTES * GIGA_BYTES
    BASES = [BYTES, KILO_BYTES, MEGA_BYTES, GIGA_BYTES, TERA_BYTES]
    NAMES = ["b", "KiB", "MiB", "GiB", "TiB"]

    __slots__ = ("__raw", "__neg", "__size", "__base")

    def __init__(self, size: int):
        raw = size
        neg = size < 0
        size = abs(size)
        self.__raw = raw
        self.__neg = neg
        self.__size = size
        self.__base = (size and min(4, int(math.log(size, 1024)))) or 0

    def __hash__(self):
        return hash(self.__raw)

    def __int__(self):
        return int(self.__raw)

    def __float__(self):
        return float(self.__raw)

    def __eq__(self, other):
        return isinstance(other, FileSize) and self.__raw == other.__raw

    def __ne__(self, other):
        return isinstance(other, FileSize) and self.__raw != other.__raw

    def __lt__(self, other):
        return isinstance(other, FileSize) and self.__raw < other.__raw

    def __gt__(self, other):
        return isinstance(other, FileSize) and self.__raw > other.__raw

    def __le__(self, other):
        return isinstance(other, FileSize) and self.__raw <= other.__raw

    def __ge__(self, other):
        return isinstance(other, FileSize) and self.__raw >= other.__raw

    def __str__(self):
        return (
            f"{'-' if self.__neg else ''}"
            f"{round(self.__size / self.BASES[self.__base], 2)} "
            f"{self.NAMES[self.__base]}"
        )
