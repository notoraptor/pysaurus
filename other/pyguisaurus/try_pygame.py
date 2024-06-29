import pygame
import pygame.freetype

import other.pyguisaurus as pg
from other.pyguisaurus.containers.scrollview import ScrollView
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
    window.controls.append(Area(500, 300, pg.colors.cyan, x=100, y=200))
    window.run()


if __name__ == "__main__":
    main()
