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

    button_clear = videre.Button("clear", on_click=clear)
    button_1 = videre.Button(
        "animator, progress bar and progressing", on_click=on_demo_animator
    )
    button_2 = videre.Button("fancy box", on_click=on_demo_fancybox, square=False)

    window.controls = [
        videre.Column(
            [
                videre.Text("Demo of many things", strong=False),
                videre.Row([button_clear]),
                videre.Row([button_1, button_2]),
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
    return videre.Column([aw, ap, videre.Progressing()])


if __name__ == "__main__":
    main()
