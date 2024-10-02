import videre
from pysaurus.core.constants import LOREM_IPSUM
from videre import TextAlign, TextWrap
from videre.layouts.column import Column
from videre.layouts.row import Row
from videre.layouts.scroll.scrollview import ScrollView
from videre.widgets.button import Button
from videre.widgets.text import Text
from videre.window import Window
from wip.symthon.symthon import E, Lambda, V


def demo_button(window: Window):
    text = Text(f"\n{LOREM_IPSUM}", size=24, wrap=videre.TextWrap.WORD)
    window.controls = [
        Column(
            [
                Row(
                    [
                        Button(
                            "wrap chars",
                            on_click=Lambda[E.setattr(text, wrap=TextWrap.CHAR)],
                        ),
                        Button(
                            "wrap words",
                            on_click=Lambda[E.setattr(text, wrap=TextWrap.WORD)],
                        ),
                    ]
                ),
                Row(
                    [
                        Button(
                            "left",
                            on_click=Lambda[E.set(V[text].align, TextAlign.LEFT)],
                        ),
                        Button(
                            "center",
                            on_click=Lambda[E.set(V[text].align, TextAlign.CENTER)],
                        ),
                        Button(
                            "right",
                            on_click=Lambda[E.set(V[text].align, TextAlign.RIGHT)],
                        ),
                        Button(
                            "justify",
                            on_click=Lambda[E.set(V[text].align, TextAlign.JUSTIFY)],
                        ),
                    ]
                ),
                Button(
                    "align none", on_click=Lambda[E.setattr(text, align=TextAlign.NONE)]
                ),
                # Zone(ScrollView(text, wrap_horizontal=True), 800, 300),
                ScrollView(text, wrap_horizontal=True, weight=1),
            ]
        )
    ]


def main():
    title = (
        "Hello World!! "
        "αβαβαβαβαβ 【DETROIT】この選択がどう繋がっていくのか！？【#2】 "
        "모든 인간은 태어날 때부터 자유로우며"
    )

    window = Window(title=title)
    demo_button(window)
    window.run()


if __name__ == "__main__":
    main()
