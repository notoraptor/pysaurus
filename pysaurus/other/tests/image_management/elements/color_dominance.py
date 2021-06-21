from pysaurus.core.miniature import Miniature
from pysaurus.other.tests.image_management.elements.spaced_points import SpacedPoints


class ColorDominance:
    __slots__ = "r", "g", "b", "rg", "rb", "gb", "rgb"

    def __init__(self):
        self.r = self.g = self.b = self.rg = self.rb = self.gb = self.rgb = 0

    def __str__(self):
        return str(self.key)

    @property
    def key(self):
        return self.r, self.g, self.b, self.rg, self.rb, self.gb, self.rgb

    def add_dom(self, r, g, b):
        self.r += r > g and r > b
        self.g += g > r and g > b
        self.b += b > r and b > g
        self.rg += r == g > b
        self.rb += r == b > g
        self.gb += g == b > r
        self.rgb += r == g == b


def get_color_signature(m: Miniature, spaced_color: SpacedPoints) -> ColorDominance:
    color_dom_sum = ColorDominance()
    for pixel in m.data():
        color_dom_sum.add_dom(
            spaced_color.nearest_point(pixel[0]),
            spaced_color.nearest_point(pixel[1]),
            spaced_color.nearest_point(pixel[2])
        )
    return color_dom_sum
