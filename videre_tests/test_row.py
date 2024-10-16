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
                    videre.Rectangle(50, 100, videre.Colors.red),
                    videre.Rectangle(60, 50, videre.Colors.green),
                    videre.Rectangle(70, 80, videre.Colors.blue),
                ],
                vertical_alignment=alignment,
            )
        ]
        image_testing(window.snapshot())
