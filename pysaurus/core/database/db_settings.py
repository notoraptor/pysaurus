from pysaurus.core.classes import AbstractSettings


class DbSettings(AbstractSettings):
    __slots__ = ("miniature_pixel_distance_radius", "miniature_group_min_size")

    def __init__(self):
        self.miniature_pixel_distance_radius = 6
        self.miniature_group_min_size = 0
