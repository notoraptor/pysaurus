class ComparisonTable:
    __slots__ = ('__type', '__n', '__table')

    def __init__(self, n, value_type=int):
        assert isinstance(n, int) and n > 1
        assert callable(value_type)
        self.__type = value_type
        self.__n = n
        self.__table = [self.__type(0) for _ in range(self.size)]

    @property
    def n(self):
        return self.__n

    @property
    def size(self):
        return self.__n * (self.__n - 1) // 2

    def get_position(self, i, j):
        if i == j:
            raise ValueError('i == j == %d' % i)
        if i > j:
            i, j = j, i
        return i * (2 * self.__n - i - 3) // 2 + j - 1

    def set(self, i, j, value):
        assert isinstance(value, self.__type)
        self.__table[self.get_position(i, j)] = value

    def get(self, i, j):
        return self.__table[self.get_position(i, j)]

    def values(self):
        return iter(self.__table)


if __name__ == '__main__':
    def main():
        table = ComparisonTable(6)
        print(table.get(0, 1))


    main()
