from typing import Callable

import pygame
import pygame.gfxdraw

from videre.core.pygame_utils import PygameUtils


class Colors:
    aliceblue = pygame.Color(240, 248, 255)
    antiquewhite = pygame.Color(250, 235, 215)
    aqua = pygame.Color(0, 255, 255)
    aquamarine = pygame.Color(127, 255, 212)
    azure = pygame.Color(240, 255, 255)
    beige = pygame.Color(245, 245, 220)
    bisque = pygame.Color(255, 228, 196)
    black = pygame.Color(0, 0, 0)
    blanchedalmond = pygame.Color(255, 235, 205)
    blue = pygame.Color(0, 0, 255)
    blueviolet = pygame.Color(138, 43, 226)
    brown = pygame.Color(165, 42, 42)
    burlywood = pygame.Color(222, 184, 135)
    cadetblue = pygame.Color(95, 158, 160)
    chartreuse = pygame.Color(127, 255, 0)
    chocolate = pygame.Color(210, 105, 30)
    coral = pygame.Color(255, 127, 80)
    cornflowerblue = pygame.Color(100, 149, 237)
    cornsilk = pygame.Color(255, 248, 220)
    crimson = pygame.Color(220, 20, 60)
    cyan = pygame.Color(0, 255, 255)
    darkblue = pygame.Color(0, 0, 139)
    darkcyan = pygame.Color(0, 139, 139)
    darkgoldenrod = pygame.Color(184, 134, 11)
    darkgray = pygame.Color(169, 169, 169)
    darkgreen = pygame.Color(0, 100, 0)
    darkkhaki = pygame.Color(189, 183, 107)
    darkmagenta = pygame.Color(139, 0, 139)
    darkolivegreen = pygame.Color(85, 107, 47)
    darkorange = pygame.Color(255, 140, 0)
    darkorchid = pygame.Color(153, 50, 204)
    darkred = pygame.Color(139, 0, 0)
    darksalmon = pygame.Color(233, 150, 122)
    darkseagreen = pygame.Color(143, 188, 139)
    darkslateblue = pygame.Color(72, 61, 139)
    darkslategray = pygame.Color(47, 79, 79)
    darkturquoise = pygame.Color(0, 206, 209)
    darkviolet = pygame.Color(148, 0, 211)
    deeppink = pygame.Color(255, 20, 147)
    deepskyblue = pygame.Color(0, 191, 255)
    dimgray = pygame.Color(105, 105, 105)
    dodgerblue = pygame.Color(30, 144, 255)
    floralwhite = pygame.Color(253, 245, 230)
    forestgreen = pygame.Color(34, 139, 34)
    fuchsia = pygame.Color(255, 0, 255)
    gainsboro = pygame.Color(220, 220, 220)
    ghostwhite = pygame.Color(248, 248, 255)
    gold = pygame.Color(255, 215, 0)
    goldenrod = pygame.Color(218, 165, 32)
    gray = pygame.Color(128, 128, 128)
    green = pygame.Color(0, 128, 0)
    greenyellow = pygame.Color(173, 255, 47)
    honeydew = pygame.Color(240, 255, 240)
    hotpink = pygame.Color(255, 105, 180)
    indianred = pygame.Color(205, 92, 92)
    indigo = pygame.Color(75, 0, 130)
    ivory = pygame.Color(255, 255, 240)
    khaki = pygame.Color(240, 230, 140)
    lavender = pygame.Color(230, 230, 250)
    lavenderblush = pygame.Color(255, 240, 245)
    lawngreen = pygame.Color(124, 252, 0)
    lemonchiffon = pygame.Color(255, 250, 205)
    lightblue = pygame.Color(173, 216, 230)
    lightcoral = pygame.Color(240, 128, 128)
    lightcyan = pygame.Color(224, 255, 255)
    lightgoldenrodyellow = pygame.Color(250, 250, 210)
    lightgray = pygame.Color(211, 211, 211)
    lightgreen = pygame.Color(144, 238, 144)
    lightpink = pygame.Color(255, 182, 193)
    lightsalmon = pygame.Color(255, 160, 122)
    lightseagreen = pygame.Color(32, 178, 170)
    lightskyblue = pygame.Color(135, 206, 250)
    lightslategray = pygame.Color(119, 136, 153)
    lightsteelblue = pygame.Color(176, 196, 222)
    lightyellow = pygame.Color(255, 255, 224)
    lime = pygame.Color(0, 255, 0)
    limegreen = pygame.Color(50, 205, 50)
    linen = pygame.Color(250, 240, 230)
    magenta = pygame.Color(255, 0, 255)
    maroon = pygame.Color(128, 0, 0)
    mediumaquamarine = pygame.Color(102, 205, 170)
    mediumblue = pygame.Color(0, 0, 205)
    mediumorchid = pygame.Color(186, 85, 211)
    mediumpurple = pygame.Color(147, 112, 219)
    mediumseagreen = pygame.Color(60, 179, 113)
    mediumslateblue = pygame.Color(123, 104, 238)
    mediumspringgreen = pygame.Color(0, 250, 154)
    mediumturquoise = pygame.Color(72, 209, 204)
    mediumvioletred = pygame.Color(199, 21, 133)
    midnightblue = pygame.Color(25, 25, 112)
    mintcream = pygame.Color(245, 255, 250)
    mistyrose = pygame.Color(255, 228, 225)
    moccasin = pygame.Color(255, 228, 181)
    navajowhite = pygame.Color(255, 222, 173)
    navy = pygame.Color(0, 0, 128)
    oldlace = pygame.Color(253, 245, 230)
    olive = pygame.Color(128, 128, 0)
    olivedrab = pygame.Color(107, 142, 35)
    orange = pygame.Color(255, 165, 0)
    orangered = pygame.Color(255, 69, 0)
    orchid = pygame.Color(218, 112, 214)
    palegoldenrod = pygame.Color(238, 232, 170)
    palegreen = pygame.Color(152, 251, 152)
    paleturquoise = pygame.Color(175, 238, 238)
    palevioletred = pygame.Color(219, 112, 147)
    papayawhip = pygame.Color(255, 239, 213)
    peachpuff = pygame.Color(255, 218, 185)
    peru = pygame.Color(205, 133, 63)
    pink = pygame.Color(255, 192, 203)
    plum = pygame.Color(221, 160, 221)
    powderblue = pygame.Color(176, 224, 230)
    purple = pygame.Color(128, 0, 128)
    rebeccapurple = pygame.Color(102, 51, 153)
    red = pygame.Color(255, 0, 0)
    rosybrown = pygame.Color(188, 143, 143)
    royalblue = pygame.Color(65, 105, 225)
    saddlebrown = pygame.Color(139, 69, 19)
    salmon = pygame.Color(250, 128, 114)
    sandybrown = pygame.Color(244, 164, 96)
    seagreen = pygame.Color(46, 139, 87)
    seashell = pygame.Color(255, 245, 238)
    sienna = pygame.Color(160, 82, 45)
    silver = pygame.Color(192, 192, 192)
    skyblue = pygame.Color(135, 206, 235)
    slateblue = pygame.Color(106, 90, 205)
    slategray = pygame.Color(112, 128, 144)
    snow = pygame.Color(255, 250, 250)
    springgreen = pygame.Color(0, 255, 127)
    steelblue = pygame.Color(70, 130, 180)
    tan = pygame.Color(210, 180, 140)
    teal = pygame.Color(0, 128, 128)
    thistle = pygame.Color(216, 191, 216)
    tomato = pygame.Color(255, 99, 7)
    turquoise = pygame.Color(64, 224, 208)
    violet = pygame.Color(238, 130, 238)
    wheat = pygame.Color(245, 222, 179)
    white = pygame.Color(255, 255, 255)
    whitesmoke = pygame.Color(245, 245, 245)
    yellow = pygame.Color(255, 255, 0)
    yellowgreen = pygame.Color(154, 205, 50)
    # Non-HTML, supplementary colors
    transparent = pygame.Color(0, 0, 0, 0)


class Gradient(PygameUtils):
    """
    Inspired from (2024/06/30): https://stackoverflow.com/a/62336993
    """

    __slots__ = ("_colors", "_vertical", "_base", "_gen")

    def __init__(self, *colors: pygame.Color, **kwargs):
        super().__init__()

        self._colors = colors or [Colors.transparent]
        self._vertical = kwargs.pop("vertical", False)
        self._base = None
        self._gen: Callable[[int, int], pygame.Surface] = (
            self._plain if len(self._colors) == 1 else self._gradient
        )

    def _plain(self, width: int, height: int) -> pygame.Surface:
        surface = self._new_surface(width, height)
        surface.fill(self._colors[0])
        return surface

    def _gradient(self, width: int, height: int) -> pygame.Surface:
        return pygame.transform.smoothscale(self._get_base(), (width, height))

    def _get_base(self):
        if self._base is None:
            if self._vertical:
                w = 2
                h = len(self._colors)
            else:
                w = len(self._colors)
                h = 2
            base = self._new_surface(w, h)
            for i, color in enumerate(self._colors):
                if self._vertical:
                    x1, x2 = 0, 1
                    y1 = y2 = i
                else:
                    x1 = x2 = i
                    y1, y2 = 0, 1
                pygame.gfxdraw.line(base, x1, y1, x2, y2, color)
            self._base = base

        return self._base

    def generate(self, width: int, height: int) -> pygame.Surface:
        return self._gen(width, height)
