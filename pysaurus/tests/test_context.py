import sys

from pysaurus.core.meta.context import Context


class Test(Context):
    def __init__(self):
        super().__init__()
        self.value = 33

    def on_exit(self):
        print('exited', file=sys.stderr)


def main():
    test = Test()
    with test:
        value = test.value
        print('value is', value, file=sys.stderr)
    print('OK', file=sys.stderr)
    print(test.value)


if __name__ == '__main__':
    main()
