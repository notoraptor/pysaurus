from videre import Button, Column, ScrollView, Text
from videre.windowing.windowfactory import WindowLD


def test_fancybox(image_testing):
    with WindowLD() as window:

        def fancy(*args):
            window.set_fancybox(
                ScrollView(Column([Text(f"Item {i + 1}") for i in range(10)])),
                buttons=[Button("yes"), Button("NO!")],
            )

        window.controls = [Button("Fancy!", on_click=fancy, square=True)]
        fancy()

        image_testing(window.snapshot())
