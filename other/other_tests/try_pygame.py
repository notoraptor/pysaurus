import pygame
from pygame import locals as L


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == L.QUIT:
                print("Quit pygame.")
                running = False
        screen.fill("white")
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == '__main__':
    main()
