class DbSettings:
    __slots__ = ("miniature_pixel_distance_radius", "miniature_group_min_size")

    def __init__(self):
        self.miniature_pixel_distance_radius = 6
        self.miniature_group_min_size = 0

    def update(self, dct: dict):
        for key in self.__slots__:
            if key in dct:
                setattr(self, key, dct[key])

    def to_dict(self):
        return {key: getattr(self, key) for key in self.__slots__}

    @classmethod
    def from_dict(cls, dct: dict):
        settings = cls()
        settings.update(dct)
        return settings
