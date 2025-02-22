import videre
from videre.layouts.div import Div


def main():
    window = videre.Window()
    work = videre.Container(padding=videre.Padding.all(10), weight=1)

    def clear(*args):
        work.control = None

    def on_container(*args):
        text = (
            "Hello, World! How are you? I'm fine, thanks, and you? I am ok, too, dear!"
        )
        parameters = {
            "padding": videre.Padding.all(50),
            "border": videre.Border.all(1),
            "weight": 1,
        }
        work.control = videre.Column(
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

    def on_demo_animator(*args):
        work.control = demo_animator()

    def on_demo_fancybox(*args):
        window.set_fancybox(
            videre.ScrollView(
                videre.Column([videre.Text(f"Item {i + 1}") for i in range(100)])
            ),
            buttons=[videre.Button("yes"), videre.Button("NO!")],
        )

    def on_alert(*args):
        window.alert("You have an alert")

    def on_text_input(*args):
        work.control = videre.TextInput(weight=1)

    window.controls = [
        videre.Column(
            [
                videre.Text("Demo of many things", strong=False),
                videre.Row([videre.Button("clear", on_click=clear)]),
                videre.Row(
                    [
                        videre.Button("container", on_click=on_container),
                        videre.Button(
                            "animator, progressing and progress bar",
                            on_click=on_demo_animator,
                        ),
                        videre.Button(
                            "fancy box", on_click=on_demo_fancybox, square=False
                        ),
                        videre.Button("alert", on_click=on_alert),
                        videre.Button("text input", on_click=on_text_input),
                    ]
                ),
                work,
            ]
        )
    ]
    on_container()
    window.run()


def demo_animator():
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


if __name__ == "__main__":
    main()
