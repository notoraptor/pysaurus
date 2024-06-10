import os

import pygame
import pygame.freetype
from pygame import locals as L

from pysaurus import package_dir


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("My PyGame Application! αβαβαβαβαβ 【DETROIT】この選択がどう繋がっていくのか！？【#2】")
    clock = pygame.time.Clock()

    font_path_1 = os.path.abspath(
        os.path.join(
            package_dir(),
            "..",
            "resource",
            "fonts",
            "source-sans",
            "TTF",
            "SourceSans3-Light.ttf",
        )
    )
    font_path_2 = os.path.abspath(
        os.path.join(
            package_dir(),
            "..",
            "resource",
            "fonts",
            "SourceHanSans-VF.ttf",
        )
    )
    font_path = font_path_2
    assert os.path.isfile(font_path)
    font = pygame.freetype.Font(font_path, 24)
    font.strong = True
    text, text_pos = font.render("Hello World! αβαβαβαβαβ 選択がどう繋がっていくのか", "black")
    print(text.get_width(), text.get_height(), text_pos)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == L.QUIT:
                print("Quit pygame.")
                running = False
        screen.fill("white")
        screen.blit(text, text_pos)
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    main()
