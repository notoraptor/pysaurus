from videre.clipboard import Clipboard
from videre.layouts.column import Column
from videre.layouts.row import Row
from videre.layouts.scroll.scrollview import ScrollView
from videre.widgets.button import Button
from videre.widgets.checkbox import Checkbox
from videre.widgets.text import Text
from videre.window import Window
from wip.symthon.symthon import E, Lambda, V


def main():
    sentence = "☐ ☑ ✅ ✓ ✔ 🗸 🗹"
    window = Window(title=sentence)
    text = Text(sentence)

    check = Button(
        "☐",
        on_click=Lambda(
            V.b,
            [
                E.if_(V.b.text == "☐", [E.setattr(V.b, text="☑")]).else_(
                    E.setattr(V.b, text="☐")
                )
            ],
        ),
    )
    # check._padx = check._pady = max(check._padx, check._pady)

    window.controls = [
        Column(
            [
                Row(
                    [
                        Button(
                            "to clipboard",
                            on_click=Lambda[V[Clipboard].set("Hello, world!")],
                        ),
                        Button(
                            "from clipboard",
                            on_click=Lambda[E.setattr(text, text=V[Clipboard].get())],
                        ),
                        check,
                        Checkbox(),
                        Text("Hello, world!"),
                    ]
                ),
                ScrollView(text, wrap_horizontal=True, weight=1),
            ]
        )
    ]

    window.run()


if __name__ == "__main__":
    main()
