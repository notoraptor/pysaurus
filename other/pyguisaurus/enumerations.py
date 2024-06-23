from enum import Enum, unique

import pygame


@unique
class MouseButton(Enum):
    BUTTON_LEFT = pygame.BUTTON_LEFT
    BUTTON_MIDDLE = pygame.BUTTON_MIDDLE
    BUTTON_RIGHT = pygame.BUTTON_RIGHT
    BUTTON_WHEELDOWN = pygame.BUTTON_WHEELDOWN
    BUTTON_WHEELUP = pygame.BUTTON_WHEELUP
    BUTTON_X1 = pygame.BUTTON_X1
    BUTTON_X2 = pygame.BUTTON_X2
