from videre import Column, ProgressBar
from videre.windowing.windowfactory import WindowLD


def main():
    window = WindowLD()
    window.controls = [
        Column(
            [
                ProgressBar(),
                ProgressBar(),
                ProgressBar(0.1),
                ProgressBar(0.5),
                ProgressBar(0.8),
                ProgressBar(0.9),
                ProgressBar(1),
            ]
        )
    ]
    window.run()


if __name__ == "__main__":
    main()
