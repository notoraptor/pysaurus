import pygame
import pygame.freetype

from other.pyguisaurus.scrollview import ScrollView
from other.pyguisaurus.text import Text
from other.pyguisaurus.window import Window


def main():
    title = (
        "Hello World!! "
        "αβαβαβαβαβ 【DETROIT】この選択がどう繋がっていくのか！？【#2】 "
        "모든 인간은 태어날 때부터 자유로우며"
    )

    pygame.init()
    text = "小松 未可子 | 🌀 hello world | " + Text.lorem_ipsum()[:10]
    window = Window(title=title)
    window.controls.append(
        ScrollView(Text(text, size=768, wrap=True), expand_children_horizontal=False)
    )
    window.run()


if __name__ == "__main__":
    main()
