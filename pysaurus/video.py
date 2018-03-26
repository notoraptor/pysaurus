from pysaurus.property import PropertyDict
from pysaurus.utils import strings
from pysaurus.utils.absolute_path import AbsolutePath
from pysaurus.utils.json_compatible import JSONCompatible
from pysaurus.utils.symbols import timestamp_microseconds, default


class Video(JSONCompatible):
    __FILE_PROPS = (strings.ABSOLUTE_PATH, strings.VIDEO_ID, strings.DATE_ADDED_MICROSECONDS,
                    strings.THUMBNAIL, strings.DATE_MODIFIED, strings.MOVIE_NAME, strings.MOVIE_TITLE)
    __PROPS = tuple(sorted((
        strings.CONTAINER_FORMAT, strings.SIZE, strings.DURATION, strings.WIDTH, strings.HEIGHT, strings.VIDEO_CODEC,
        strings.AUDIO_CODEC, strings.FRAME_RATE, strings.SAMPLE_RATE
    )))
    __slots__ = __FILE_PROPS + __PROPS + (strings.PROPERTIES, 'updated')

    def __init__(self, properties=None, updated=False, **kwargs):
        assert isinstance(kwargs[strings.ABSOLUTE_PATH], str)

        self.absolute_path = AbsolutePath(kwargs[strings.ABSOLUTE_PATH])
        self.video_id = kwargs[strings.VIDEO_ID]
        self.date_added_microseconds = default(kwargs, strings.DATE_ADDED_MICROSECONDS, timestamp_microseconds)
        self.thumbnail = kwargs.get(strings.THUMBNAIL, None)  # type: AbsolutePath
        self.date_modified = default(kwargs, strings.DATE_MODIFIED, self.absolute_path.get_date_modified)
        self.movie_name = kwargs[strings.MOVIE_NAME]
        self.movie_title = kwargs[strings.MOVIE_TITLE]
        self.container_format = kwargs[strings.CONTAINER_FORMAT]
        self.size = kwargs[strings.SIZE]
        self.duration = kwargs[strings.DURATION]
        self.width = kwargs[strings.WIDTH]
        self.height = kwargs[strings.HEIGHT]
        self.video_codec = kwargs[strings.VIDEO_CODEC]
        self.audio_codec = kwargs[strings.AUDIO_CODEC]
        self.frame_rate = kwargs[strings.FRAME_RATE]
        self.sample_rate = kwargs[strings.SAMPLE_RATE]
        self.properties = properties
        self.updated = bool(updated)

        if self.thumbnail is not None:
            self.thumbnail = AbsolutePath.ensure(self.thumbnail)

        assert isinstance(self.video_id, int)
        assert isinstance(self.date_added_microseconds, int)
        assert isinstance(self.date_modified, float)
        assert isinstance(self.movie_name, (str, type(None)))
        assert isinstance(self.movie_title, (str, type(None)))
        assert isinstance(self.container_format, str)
        assert isinstance(self.size, int)
        assert isinstance(self.duration, int)
        assert isinstance(self.width, int)
        assert isinstance(self.height, int)
        assert isinstance(self.video_codec, str)
        assert isinstance(self.frame_rate, float)
        assert isinstance(self.audio_codec, (str, type(None)))
        assert isinstance(self.sample_rate, (int, float, type(None)))
        assert isinstance(self.properties, (PropertyDict, type(None)))

    title = property(lambda self: self.movie_name or self.movie_title or self.absolute_path.title)
    characteristics = property(lambda self: tuple(getattr(self, prop_name) for prop_name in self.__PROPS))

    def set_properties(self, properties):
        assert isinstance(properties, (PropertyDict, type(None)))
        self.properties = properties
        self.updated = True

    def has_valid_thumbnail(self):
        return self.thumbnail is not None and self.thumbnail.exists() and self.thumbnail.isfile()

    def set_thumbnail(self, thumbnail: AbsolutePath):
        self.thumbnail = thumbnail
        self.updated = True

    def delete_thumbnail(self):
        if self.has_valid_thumbnail():
            self.thumbnail.delete()
            assert not self.thumbnail.exists()
            self.thumbnail = None
            self.updated = True

    def to_json_data(self):
        # Don't save attribute 'updated'.
        json_dict = {key: getattr(self, key) for key in self.__slots__[:-1]}
        json_dict[strings.ABSOLUTE_PATH] = str(self.absolute_path)
        json_dict[strings.THUMBNAIL] = str(self.thumbnail) if self.thumbnail else None
        if self.properties is not None:
            json_dict[strings.PROPERTIES] = self.properties.to_json_data()
        return json_dict

    @classmethod
    def from_json_data(cls, json_data, property_type_set=None):
        """
        :rtype: Video
        """
        json_properties = json_data.pop(strings.PROPERTIES, None)
        if json_properties is not None:
            json_data[strings.PROPERTIES] = PropertyDict.from_json_data(json_properties, property_type_set)
        elif property_type_set is not None:
            json_data[strings.PROPERTIES] = PropertyDict(property_type_set)
        return cls(**json_data)
