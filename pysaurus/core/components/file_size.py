from pysaurus.core.utils import constants


class FileSize(object):
    __slots__ = ('__size', '__unit')

    def __init__(self, size):
        # type: (int) -> None
        self.__size = size
        self.__unit = constants.BYTES
        for unit in (constants.TERA_BYTES, constants.GIGA_BYTES, constants.MEGA_BYTES, constants.KILO_BYTES):
            if size // unit:
                self.__unit = unit
                break

    @property
    def value(self):
        return self.__size

    @property
    def nb_units(self):
        return self.__size / self.__unit

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return isinstance(other, FileSize) and self.value == other.value

    def __lt__(self, other):
        return isinstance(other, FileSize) and self.value < other.value

    def __str__(self):
        return '%s %s' % (round(self.nb_units, 2), constants.SIZE_UNIT_TO_STRING[self.__unit])
