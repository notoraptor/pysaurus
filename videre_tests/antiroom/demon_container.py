import videre
from videre.core.sides.padding import Padding


def main():
    window = videre.Window()
    window.controls = [
        videre.Container(
            videre.Text("Hello, World!"),
            background_color="yellow",
            border=videre.Border(
                top=(100, videre.Colors.pink),
                left=(50, (1, 255, 2)),
                bottom=(200, videre.Colors.cyan),
                right=25,
            ),
            padding=Padding(top=385, left=100, bottom=20),
            vertical_alignment=videre.Alignment.END,
            horizontal_alignment=videre.Alignment.CENTER,
        )
    ]
    window.run()


if __name__ == "__main__":
    main()
