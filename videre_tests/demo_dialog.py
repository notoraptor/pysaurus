from videre.dialog import Dialog
from videre.layouts.column import Column
from videre.widgets.button import Button
from videre.widgets.text import Text
from videre.window import Window
from wip.symthon.symthon import E, Lambda, V


def main():
    window = Window()

    text = Text("no file chosen ...")

    def on_click(*args):
        path = Dialog.select_file_to_open()
        if path:
            text.text = "File chosen: " + path
        else:
            text.text = "You have not chosen any file!"

    l_on_click = Lambda[
        E.set(V.path, V[Dialog].select_file_to_open()),
        E.if_(V.path, [E.setattr(text, text="File chosen: " + V.path)]).else_(
            E.setattr(text, text="You have not chosen any file!")
        ),
    ]

    button = Button("Choose file", on_click=l_on_click)
    window.controls = [Column([button, text])]

    window.run()


if __name__ == "__main__":
    main()
