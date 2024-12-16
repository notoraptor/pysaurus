import logging

import videre
from videre.layouts.animator import Animator
from videre.widgets.progressing import Progressing
from videre.windowing.windowfactory import WindowLD


def main():
    logging.basicConfig(level=logging.WARNING)
    window = WindowLD()
    b1 = videre.Button("")
    b2 = videre.Button("hello")
    b3 = videre.Button("Hello")
    br = videre.Radio(None)
    bc = videre.Checkbox()

    label = videre.Text("Frame 0")

    def on_label_frame(w, f):
        label.text = f"Frame {f}"

    pb = videre.ProgressBar()

    def on_pb_frame(w, f):
        pb.value = (f % 31) / 30

    aw = Animator(label, on_frame=on_label_frame)
    ap = Animator(pb, on_frame=on_pb_frame, fps=30)
    window.controls = [videre.Column([b1, b2, b3, br, bc, aw, ap, Progressing()])]
    window.run()


if __name__ == "__main__":
    main()
