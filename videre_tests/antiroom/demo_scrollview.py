import logging

import videre
from pysaurus.core.constants import LOREM_IPSUM


def main():
    logging.basicConfig(level=logging.WARN)
    window = videre.Window()
    window.controls = [
        videre.ScrollView(
            videre.Column(
                [
                    videre.Text("Hello"),
                    videre.Text("World"),
                    videre.Text("This is a test"),
                    videre.Text("of the scroll view"),
                    videre.Text("in the antiroom demo."),
                    videre.Row(
                        [
                            videre.Text("Hello"),
                            videre.Text("World"),
                            videre.ScrollView(
                                videre.Text(LOREM_IPSUM, wrap=videre.TextWrap.WORD),
                                # wrap_horizontal=True,
                                # wrap_vertical=False,
                                weight=1,
                                key="scrollview2",
                            ),
                        ]
                    ),
                    videre.Text(LOREM_IPSUM, wrap=videre.TextWrap.WORD),
                ]
            ),
            wrap_horizontal=True,
            wrap_vertical=False,
            key="scrollview1",
        )
    ]
    window.run()


if __name__ == "__main__":
    main()
