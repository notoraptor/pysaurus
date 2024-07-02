import pygame
import pygame.freetype

from videre.containers.column import Column
from videre.containers.scrollwidget.scrollview import ScrollView
from videre.containers.zone import Zone
from videre.utils.pygame_font_factory import FONT_FACTORY
from videre.widgets.area import Area
from videre.widgets.button import Button
from videre.widgets.text import Text
from videre.window import Window
from pysaurus.core.constants import LOREM_IPSUM
from videre.colors import Colors


def main():
    title = (
        "Hello World!! "
        "αβαβαβαβαβ 【DETROIT】この選択がどう繋がっていくのか！？【#2】 "
        "모든 인간은 태어날 때부터 자유로우며"
    )

    pygame.init()
    text = "小松 未可子 | 🌀 hello world | " + FONT_FACTORY.lorem_ipsum()
    text = "\t\n" + LOREM_IPSUM
    window = Window(title=title)
    window.controls.append(
        Zone(
            ScrollView(Text(text, size=32, wrap=True), expand_children_horizontal=True),
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
    window.run()


if __name__ == "__main__":
    main()
