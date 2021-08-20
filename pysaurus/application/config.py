class Config:
    __slots__ = ("language",)

    def __init__(self):
        self.language = "english"

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
