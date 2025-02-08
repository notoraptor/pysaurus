import videre


def main():
    window = videre.Window()
    work = videre.Container(
        background_color=videre.Colors.yellow, padding=videre.Padding.all(10), weight=1
    )

    def clear(*args):
        work.control = None

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

    button_clear = videre.Button("clear", on_click=clear)
    button_1 = videre.Button(
        "animator, progressing and progress bar", on_click=on_demo_animator
    )
    button_2 = videre.Button("fancy box", on_click=on_demo_fancybox, square=False)
    button_3 = videre.Button("alert", on_click=on_alert)
    button_4 = videre.Button("text input", on_click=on_text_input)

    window.controls = [
        videre.Column(
            [
                videre.Text("Demo of many things", strong=False),
                videre.Row([button_clear]),
                videre.Row([button_1, button_2, button_3, button_4]),
                work,
            ]
        )
    ]
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


def call(args, code):
    pass


def test():
    x = 1
    y = 2
    my_function = call((x, y), "x = y + 2*x")


if __name__ == "__main__":
    main()
