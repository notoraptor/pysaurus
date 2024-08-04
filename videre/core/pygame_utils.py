import pygame


class PygameUtils:
    __slots__ = ()

    @classmethod
    def _new_surface(cls, width: int, height: int) -> pygame.Surface:
        return pygame.Surface((width, height), flags=pygame.SRCALPHA)
