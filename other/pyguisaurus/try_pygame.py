import pygame
import pygame.freetype

import other.pyguisaurus as pg
from other.pyguisaurus.containers.column import Column
from other.pyguisaurus.containers.scrollwidget.scrollview import ScrollView
from other.pyguisaurus.containers.zone import Zone
from other.pyguisaurus.utils.pygame_font_factory import FONT_FACTORY
from other.pyguisaurus.widgets.area import Area
from other.pyguisaurus.widgets.text import Text
from other.pyguisaurus.window import Window


def main():
    title = (
        "Hello World!! "
        "αβαβαβαβαβ 【DETROIT】この選択がどう繋がっていくのか！？【#2】 "
        "모든 인간은 태어날 때부터 자유로우며"
    )

    pygame.init()
    text = "小松 未可子 | 🌀 hello world | " + FONT_FACTORY.lorem_ipsum()[:10]
    window = Window(title=title)
    window.controls.append(
        Zone(
            ScrollView(
                Text(text, size=768, wrap=True), expand_children_horizontal=False
            ),
            width=800,
            height=400,
            x=100,
            y=100,
        )
    )
    window.controls.clear()
    window.controls.append(
        Area(500, 300, [pg.colors.blue, pg.colors.red], x=100, y=200)
    )
    window.controls.clear()
    window.controls.append(
        ScrollView(
            Column(
                [
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
