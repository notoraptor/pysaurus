import pygame
import pygame.freetype
from pygame import locals as L

from resource.fonts import PATH_SOURCE_HAN_SANS_TTC


def main():
    text = (
        "Hello World! My PyGame Application! "
        "αβαβαβαβαβ 【"
        "DETROIT】この選択がどう繋がっていくのか！？【#2】"
    )

    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption(text)
    clock = pygame.time.Clock()

    font_path = PATH_SOURCE_HAN_SANS_TTC
    font = pygame.freetype.Font(font_path, 24, font_index=5)
    text, text_pos = font.render(text, "black")
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
