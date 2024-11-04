import logging

import videre
from videre.widgets.animated_widget import AnimatedWidget
from videre.windowing.windowfactory import WindowLD


def main():
    logging.basicConfig(level=logging.INFO)
    window = WindowLD()
    b1 = videre.Button("")
    b2 = videre.Button("hello")
    b3 = videre.Button("Hello")
    br = videre.Radio(None)
    bc = videre.Checkbox()
    aw = AnimatedWidget(framerate=1)
    window.controls = [videre.Column([b1, b2, b3, br, bc, aw])]
    # print("b", b1.rendered_height)
    # print("b:hello", b2.rendered_height)
    # print("b:Hello", b3.rendered_height)
    # print("radio", br.rendered_height)
    # print("checkbox", br.rendered_height)
    # print("standard", window.fonts.standard_size)
    window.run()


if __name__ == "__main__":
    main()
