from videre import Column, ProgressBar
from videre.windowing.windowfactory import WindowLD


def test_progressbar(image_testing):
    with WindowLD() as window:
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
        image_testing(window.snapshot())
