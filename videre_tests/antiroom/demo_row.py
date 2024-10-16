import videre
from videre.windowing.windowfactory import WindowLD


def main():
    window = WindowLD()
    window.controls = [
        videre.Column(
            [
                videre.Rectangle(50, 100, videre.Colors.red),
                videre.Rectangle(60, 50, videre.Colors.green),
                videre.Rectangle(70, 80, videre.Colors.blue),
            ],
            horizontal_alignment=videre.Alignment.END,
        )
    ]
    window.run()


if __name__ == "__main__":
    main()
