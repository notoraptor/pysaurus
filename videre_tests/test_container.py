import videre
from videre.core.sides.padding import Padding
from videre.windowing.windowfactory import WindowLD


def test_container(image_testing):
    with WindowLD() as window:
        window.controls = [
            videre.Container(
                videre.Text("Hello, World!"),
                background_color="yellow",
                border=videre.Border(
                    top=(100, videre.Colors.red),
                    left=(50, (1, 255, 2)),
                    bottom=(200, videre.Colors.cyan),
                    right=25,
                ),
                padding=Padding(top=385, left=100, bottom=20),
                vertical_alignment=videre.Alignment.END,
                horizontal_alignment=videre.Alignment.CENTER,
            )
        ]
        image_testing(window.snapshot())

