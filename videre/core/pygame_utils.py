import pygame


class PygameUtils:
    __slots__ = ()

    def __init__(self):
        # Init pygame here.
        pygame.init()

    @classmethod
    def new_surface(cls, width: int, height: int) -> pygame.Surface:
        return pygame.Surface((width, height), flags=pygame.SRCALPHA)
