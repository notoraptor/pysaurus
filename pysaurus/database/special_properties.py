from abc import abstractmethod

from pysaurus.properties.properties import PropType
from pysaurus.video.video import Video


class SpecialPropType(PropType):
    __slots__ = ()

    @abstractmethod
    def get(self, video: Video):
        raise NotImplementedError()


class PropError(SpecialPropType):
    __slots__ = ()

    def __init__(self):
        super().__init__("<error>", "", True)

    def get(self, video: Video):
        return sorted(set(video.errors) | set(video.get_property(self.name, ())))


class SpecialProperties:
    # properties = [PropError()]
    properties = []

    @classmethod
    def install(cls, database):
        to_save = False
        for expected in cls.properties:
            if not database.has_prop_type(
                name=expected.name,
                with_type=expected.type,
                with_enum=expected.enumeration,
                default=expected.default,
            ):
                database.remove_prop_type(expected.name, save=False)
                database.add_prop_type(expected, save=False)
                to_save = True
        if to_save:
            database.save()

    @classmethod
    def all_in(cls, video: Video):
        return all(video.has_property(prop.name) for prop in cls.properties)

    @classmethod
    def set(cls, video: Video):
        for prop in cls.properties:
            video.set_property(prop.name, prop.get(video))
