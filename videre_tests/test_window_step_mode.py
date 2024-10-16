from videre import Window


def test_window_step_mode(image_regression):
    with Window("Hello world!", 800, 600) as window:
        image = window.screenshot()
        image_regression.check(image.getvalue(), diff_threshold=0)
