import videre
from pysaurus.core.constants import LOREM_IPSUM
from videre import Colors
from videre.layouts.column import Column
from videre.layouts.scroll.scrollview import ScrollView
from videre.layouts.zone import Zone
from videre.widgets.area import Area
from videre.widgets.button import Button
from videre.widgets.text import Text
from videre.window import Window


def demo(window: Window):
    text = "小松 未可子 | 🌀 hello world | " + window.fonts.provider.lorem_ipsum()
    text = "\t\n" + LOREM_IPSUM
    window.controls.append(
        Zone(
            ScrollView(Text(text, size=32, wrap=True), wrap_horizontal=True),
            width=800,
            height=400,
            # x=100,
            # y=100,
        )
    )
    if 0 / 1:
        window.controls.clear()
        window.controls.append(Area(500, 300, [Colors.blue, Colors.red], x=100, y=200))
        window.controls.clear()
        window.controls.append(
            ScrollView(
                Column(
                    [
                        Button("aeiourmn".upper()),
                        Text("Hello!"),
                        Text("How are you?"),
                        Text("I'm fine, thanks, and you?"),
                        Text("I'm fine, too, thanks !"),
                        Text("Item 1"),
                        Text("Item 2"),
                        Text("Item 3"),
                        Text("Item 4"),
                        Text("Item 5"),
                        Text("Item 6"),
                        Text("Item 7"),
                        # Text(FONT_FACTORY.lorem_ipsum()),
                    ]
                )
            )
        )


def demo_scroll_view(window: Window):
    text = "hello world lorem ipsum"
    text = "小松 未可子 | 🌀 hello world lorem ipsum | " + window.fonts.provider.lorem_ipsum(
        8, "\n"
    )
    text = LOREM_IPSUM
    window.controls = [
        ScrollView(
            Text(
                f"\t\v\t\b {text}",
                size=24,
                wrap=videre.TextWrap.CHAR,
                align=videre.TextAlign.LEFT,
            ),
            wrap_horizontal=True,
        )
    ]
