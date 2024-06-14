import pygame
import pygame.freetype
from pygame import locals as L

from resource.fonts import (
    PATH_NOTO_FANGSONG_ROTATED,
    PATH_NOTO_FANGSONG_VERTICAL,
    PATH_SOURCE_HAN_SANS_JP,
    PATH_SOURCE_HAN_SANS_TTC,
)


def main():
    title = (
        "Hello World!! "
        "αβαβαβαβαβ 【DETROIT】この選択がどう繋がっていくのか！？【#2】 "
        "모든 인간은 태어날 때부터 자유로우며"
    )

    other_text = (
        """
    C 中 J 日 K 韓 
    Simp Ch 汉文
    Trad Ch 漢
    Kanji 見る白白い
    Hira かわいい|可愛い
    kata コンピュータ 
    kor 국립국어원
    """.strip()
        .replace("\r", " ")
        .replace("\n", " ")
    )

    text_chinese = "仿宋体"

    pygame.init()
    screen = pygame.display.set_mode((1920, 720))
    pygame.display.set_caption(title)
    clock = pygame.time.Clock()

    font_path_1 = PATH_SOURCE_HAN_SANS_JP
    font_path_2 = PATH_SOURCE_HAN_SANS_TTC
    font_path_3 = PATH_NOTO_FANGSONG_ROTATED
    font_path_4 = PATH_NOTO_FANGSONG_VERTICAL
    font = pygame.freetype.Font(font_path_3, 24)
    # font.strong = True
    # font.strength = 1/16
    text, text_pos = font.render(text_chinese, "black")
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
