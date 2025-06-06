import videre
from videre.windowing.windowfactory import WindowLD


def test_rendered_button_sizes(image_testing):
    with WindowLD() as window:
        b1 = videre.Button("")
        bs = videre.Button(" ")
        b2 = videre.Button("hello")
        b3 = videre.Button("Hello")
        br = videre.Radio(None)
        bc = videre.Checkbox()
        window.controls = [
            videre.Column(
                [b1, bs, b2, b3, br, bc], horizontal_alignment=videre.Alignment.CENTER
            )
        ]
        window.render()
        print()
        print("b:empty", b1.rendered_height)
        print("b:space", bs.rendered_height)
        print("b:hello", b2.rendered_height)
        print("b:Hello", b3.rendered_height)
        print("radio", br.rendered_height)
        print("checkbox", bc.rendered_height)
        print("standard", window.fonts.font_height)
        image_testing(window.snapshot())
