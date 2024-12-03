import videre
from pysaurus.core.constants import LOREM_IPSUM


def main():
    lorem_ipsum = f"\n\n{LOREM_IPSUM}"

    window = videre.Window()
    window.controls = [videre.Text(lorem_ipsum, wrap=videre.TextWrap.WORD, color="red")]
    window.run()


if __name__ == "__main__":
    main()
