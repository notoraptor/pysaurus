import videre
from videre import Button, Checkbox, Column, Label, Radio, RadioGroup, Row
from wip.symthon.symthon import E, Lambda, V


def main():
    sentence = "☐ ☑ ✅ ✓ ✔ 🗸 🗹 ◉ ○"
    window = videre.Window(title=sentence)
    text = videre.Text(sentence)

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

    label = videre.Text("Hello world!")
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
                            on_click=Lambda[V[window].set_clipboard("Hello, world!")],
                        ),
                        Button(
                            "from clipboard",
                            on_click=Lambda[
                                E.setattr(text, text=V[window].get_clipboard())
                            ],
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
                    ],
                    vertical_alignment=videre.Alignment.CENTER,
                ),
                videre.ScrollView(text, wrap_horizontal=True, weight=1),
            ]
        )
    ]

    window.run()


if __name__ == "__main__":
    main()
