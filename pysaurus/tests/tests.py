from pysaurus.core.classes import ListView


class Test:
    def test_list_view(self):
        sequence = list(range(100))
        view = ListView(sequence, 50, 1000)  # type: ListView[int]
        assert len(view) == 50
        assert view[0] == 50
        assert view[-1] == 99
        assert len(ListView(sequence, 100, 50)) == 0
        assert len(ListView(sequence, -2, -1)) == 1
        assert list(view) == sequence[50:1000]


def main():
    test = Test()
    for field in sorted(dir(test)):
        if field.startswith('test_') and callable(getattr(test, field)):
            print(field, '...', end='')
            getattr(test, field)()
            print(' ok')


if __name__ == '__main__':
    main()
