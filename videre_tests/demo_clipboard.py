from videre.clipboard import Clipboard
from videre.layouts.column import Column
from videre.layouts.row import Row
from videre.layouts.scroll.scrollview import ScrollView
from videre.widgets.button import Button
from videre.widgets.text import Text
from videre.window import Window
from wip.symthon.symthon import E, Lambda, V


def main():
    window = Window()

    text = Text("...")
    window.controls = [
        Column([
            Row([
                Button("to clipboard", on_click=Lambda[V[Clipboard].set("Hello, world!")]),
                Button("from clipboard", on_click=Lambda[E.setattr(text, text=V[Clipboard].get())]),
            ]),
            ScrollView(text, wrap_horizontal=True)
        ]),
    ]

    window.run()


if __name__ == '__main__':
    main()
