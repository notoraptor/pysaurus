import logging

import videre
from pysaurus.core.constants import LOREM_IPSUM
from pysaurus.core.functions import get_tagged_methods
from videre.layouts.div import Div

logger = logging.getLogger(__name__)


class DemoDecorator:
    def __init__(self):
        self.rank = 0

    def __call__(self, title=""):
        order = self.rank + 1
        self.rank += 1

        def decorator(function):
            name = title or function.__name__.replace("_", " ")
            function.demo_title = f"({order}) {name}"
            return function

        return decorator


on_demo = DemoDecorator()


class Demo:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)

        self.window = videre.Window()
        self.work = videre.Container(padding=videre.Padding.all(10), weight=1)

        self.demos = get_tagged_methods(self, "demo_title")
        buttons = [
            videre.Button(title, on_click=self._demo_from(function))
            for title, function in sorted(self.demos.items())
        ]
        self.window.controls = [
            videre.Column(
                [
                    videre.Text("Demo of many things", strong=False),
                    videre.Row([videre.Button("clear", on_click=self.clear)]),
                    videre.Row(buttons),
                    self.work,
                ]
            )
        ]

    def _demo_from(self, function):
        def wrapper(*args):
            ret = function(*args)
            if ret is not None:
                self.work.control = ret

        return wrapper

    def start(self):
        first_demo_title = sorted(self.demos.keys())[0]
        first_demo = self.demos[first_demo_title]
        self._demo_from(first_demo)()
        self.window.run()

    def clear(self, *args):
        self.work.control = None

    @on_demo("scroll view")
    def on_scroll_view(self, *args):
        return videre.ScrollView(
            videre.Column(
                [
                    videre.Text("Hello"),
                    videre.Text("World"),
                    videre.Text("This is a test"),
                    videre.Text("of the scroll view"),
                    videre.Text("in the antiroom demo."),
                    videre.Row(
                        [
                            videre.Text("Hello"),
                            videre.Text("World"),
                            videre.ScrollView(
                                videre.Text(LOREM_IPSUM, wrap=videre.TextWrap.WORD),
                                # wrap_horizontal=True,
                                # wrap_vertical=False,
                                weight=1,
                                key="scrollview2",
                            ),
                        ]
                    ),
                    videre.Text(LOREM_IPSUM, wrap=videre.TextWrap.WORD),
                ]
            ),
            wrap_horizontal=True,
            wrap_vertical=False,
            key="scrollview1",
        )

    @on_demo("container")
    def on_container(self, *args):
        text = (
            "Hello, World! How are you? I'm fine, thanks, and you? I am ok, too, dear!"
        )
        parameters = {
            "padding": videre.Padding.all(50),
            "border": videre.Border.all(1),
            "weight": 1,
        }
        return videre.Column(
            [
                videre.Container(
                    videre.Text(text),
                    **parameters,
                    horizontal_alignment=videre.Alignment.START,
                ),
                Div(videre.Text(text, wrap=videre.TextWrap.WORD), weight=1),
                videre.Button(text, weight=1),
                videre.Container(
                    videre.Text(text),
                    **parameters,
                    horizontal_alignment=videre.Alignment.CENTER,
                ),
                videre.Container(
                    videre.Text(text),
                    **parameters,
                    horizontal_alignment=videre.Alignment.END,
                ),
            ]
        )

    @on_demo("Animator, progressing and progress bars")
    def on_demo_animator(self, *args):
        label = videre.Text("Frame 0")

        def on_label_frame(w, f):
            label.text = f"Frame {f}"

        pb = videre.ProgressBar()

        def on_pb_frame(w, f):
            pb.value = (f % 31) / 30

        aw = videre.Animator(label, on_frame=on_label_frame)
        ap = videre.Animator(pb, on_frame=on_pb_frame, fps=30)
        return videre.Column(
            [
                aw,
                ap,
                videre.Progressing(),
                videre.ProgressBar(),
                videre.ProgressBar(),
                videre.ProgressBar(0.1),
                videre.ProgressBar(0.5),
                videre.ProgressBar(0.8),
                videre.ProgressBar(0.9),
                videre.ProgressBar(1),
            ]
        )

    @on_demo("text input")
    def on_text_input(self, *args):
        return videre.TextInput(weight=1)

    @on_demo("fancybox")
    def on_demo_fancybox(self, *args):
        self.window.set_fancybox(
            videre.ScrollView(
                videre.Column([videre.Text(f"Item {i + 1}") for i in range(100)])
            ),
            buttons=[videre.Button("yes"), videre.Button("NO!")],
        )

    @on_demo("alert")
    def on_alert(self, *args):
        self.window.alert("You have an alert")


def main():
    Demo().start()


if __name__ == "__main__":
    main()
