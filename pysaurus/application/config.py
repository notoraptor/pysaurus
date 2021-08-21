from pysaurus.core.classes import AbstractSettings


class Config(AbstractSettings):
    __slots__ = ("language",)

    def __init__(self):
        self.language = "english"
