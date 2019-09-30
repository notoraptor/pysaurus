from pysaurus.core.functions import string_to_pieces


def test_string_to_pieces():
    print(string_to_pieces("I_can't stand              your attitude! Morron!"))


if __name__ == '__main__':
    test_string_to_pieces()
