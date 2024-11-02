import pytest

import videre
from videre.windowing.windowfactory import WindowLD


@pytest.mark.parametrize(
    "alignment", [videre.Alignment.START, videre.Alignment.CENTER, videre.Alignment.END]
)
def test_row(alignment, image_testing):
    with WindowLD() as window:
        window.controls = [
            videre.Row(
                [
                    videre.Container(
                        width=50, height=100, background_color=videre.Colors.red
                    ),
                    videre.Container(
                        width=60, height=50, background_color=videre.Colors.green
                    ),
                    videre.Container(
                        width=70, height=80, background_color=videre.Colors.blue
                    ),
                ],
                vertical_alignment=alignment,
            )
        ]
        image_testing(window.snapshot())
