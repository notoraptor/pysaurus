from typing import Dict, List, Tuple, Union

import pygame


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


ColorDefinition = Union[
    pygame.Color, Tuple[int, int, int], Tuple[int, int, int, int], List[int], str, None
]


def parse_color(value: ColorDefinition) -> pygame.Color:
    """
    Parse color.
    Options:
        parse_color((r, g, b))
        parse_color((r, g, b, a))
        parse_color([r, g, b])
        parse_color([r, g, b, a])
        parse_color("#<hex>")
            Examples:
                #0bffff (alpha value will be 255)
                #0bff1bee (alpha value will be 0xee)
        parse_color("<color_name>")
            For valid color names, see members of class videre.Colors
        parse_color(pygame.Color)
            Return given color.
    :return: a pygame.Color object.
    """
    if isinstance(value, pygame.Color):
        return value
    elif isinstance(value, (tuple, list)):
        if len(value) not in (3, 4):
            raise ValueError(
                f"Color tuple/list must have 3 or 4 values, got {len(value)}"
            )
        return pygame.Color(*value)
    elif isinstance(value, str):
        if not value:
            raise ValueError("Expected a non-empty string color")
        if value[0] == "#":
            hex_code = value[1:]
            if len(hex_code) > 8:
                raise ValueError(
                    f"Too long color hex (at most 8 digits expected): {value}"
                )
            color_integer = int(hex_code, 16)
            v1 = color_integer >> (3 * 8)
            v2 = (color_integer & 0xFFFFFF) >> (2 * 8)
            v3 = (color_integer & 0xFFFF) >> (1 * 8)
            v4 = color_integer & 0xFF
            if v1:
                r, g, b, a = v1, v2, v3, v4
            else:
                r, g, b, a = v2, v3, v4, 255
            return pygame.Color(r, g, b, a)
        else:
            color = getattr(Colors, value, None)
            if not isinstance(color, pygame.Color):
                raise ValueError(f"Unknown color name: {value}")
            return color
    elif value is None:
        return Colors.transparent
    else:
        raise ValueError(f"Unsupported color definition: {type(value).__name__}")


class _ColorToString:
    __slots__ = ["_color_to_name"]

    def __init__(self):
        self._color_to_name: Dict[Tuple[int, int, int, int], str] = {}
        for name in dir(Colors):
            if "a" <= name[0] <= "z":
                val = getattr(Colors, name)
                if isinstance(val, pygame.Color):
                    self._color_to_name[(val.r, val.g, val.b, val.a)] = name

    def __call__(self, color: pygame.Color) -> str:
        color_tuple = (color.r, color.g, color.b, color.a)
        if color_tuple not in self._color_to_name:
            name = "#"
            values = color_tuple if color.a != 255 else (color.r, color.g, color.b)
            for value in values:
                assert isinstance(value, int)
                assert 0 <= value < 256
                name += hex(value)[2:].ljust(2, "0")
            self._color_to_name[color_tuple] = name
        return self._color_to_name[color_tuple]


stringify_color = _ColorToString()
