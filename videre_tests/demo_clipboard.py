from videre.clipboard import Clipboard
from videre.layouts.column import Column
from videre.layouts.radiogroup import RadioGroup
from videre.layouts.row import Row
from videre.layouts.scroll.scrollview import ScrollView
from videre.widgets.button import Button
from videre.widgets.checkbox import Checkbox
from videre.widgets.label import Label
from videre.widgets.radio import Radio
from videre.widgets.text import Text
from videre.window import Window
from wip.symthon.symthon import E, Lambda, V


def main():
    sentence = "☐ ☑ ✅ ✓ ✔ 🗸 🗹 ◉ ○"
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

    label = Text("Hello world!")
    checkbox = Checkbox(
        on_change=Lambda(
            V.checkbox,
            [
                E.setattr(
                    label,
                    text=E.cond(
                        V.checkbox.checked, "Box is checked!", "Box is not checked!"
                    ),
                )
            ],
        )
    )

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
                        Radio("something"),
                        checkbox,
                        label,
                        RadioGroup(
                            Row(
                                [
                                    Radio("a", key="radio_a"),
                                    Radio("b"),
                                    Radio("c"),
                                    Radio("d"),
                                ]
                            ),
                            can_deselect=False,
                            value="b",
                            on_change=Lambda(V.rg, [E.print(V.rg.value)]),
                        ),
                        Label(for_button="radio_a", text="Click to select radio A"),
                        Label(for_button=checkbox, text="check!"),
                    ]
                ),
                ScrollView(text, wrap_horizontal=True, weight=1),
            ]
        )
    ]

    window.run()


if __name__ == "__main__":
    main()
