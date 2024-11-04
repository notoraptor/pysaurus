import videre
from videre.windowing.windowfactory import WindowLD


def main():
    with WindowLD() as window:
        b1 = videre.Button("")
        b2 = videre.Button("hello")
        b3 = videre.Button("Hello")
        br = videre.Radio(None)
        bc = videre.Checkbox()
        window.controls = [videre.Column([b1, b2, b3, br, bc])]
        window.render()
        print("b", b1.rendered_height)
        print("b:hello", b2.rendered_height)
        print("b:Hello", b3.rendered_height)
        print("radio", br.rendered_height)
        print("checkbox", br.rendered_height)
        print("standard", window.fonts.standard_size)


if __name__ == "__main__":
    main()
