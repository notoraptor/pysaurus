import pytest

import videre


@pytest.mark.parametrize(
    "alignment", [videre.Alignment.START, videre.Alignment.CENTER, videre.Alignment.END]
)
def test_row(alignment, fake_win):
    fake_win.controls = [
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
    fake_win.check()
