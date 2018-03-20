from pysaurus.property import PropertyDict
from pysaurus.utils import strings
from pysaurus.utils.absolute_path import AbsolutePath
from pysaurus.utils.json_compatible import JSONCompatible
from pysaurus.utils.symbols import timestamp_microseconds, default


class Video(JSONCompatible):
    __FILE_PROPS = [strings.ABSOLUTE_PATH, strings.VIDEO_ID, strings.DATE_ADDED_MICROSECONDS,
                    strings.THUMBNAIL, strings.DATE_MODIFIED]
    __PROPS = list(sorted([
        strings.CONTAINER_FORMAT, strings.SIZE, strings.DURATION, strings.WIDTH, strings.HEIGHT, strings.VIDEO_CODEC,
        strings.AUDIO_CODEC, strings.FRAME_RATE, strings.SAMPLE_RATE
    ]))
    __slots__ = __FILE_PROPS + __PROPS + [strings.PROPERTIES, 'updated']

    def __init__(self, properties=None, updated=False, **kwargs):
        assert isinstance(kwargs[strings.ABSOLUTE_PATH], str)

        self.absolute_path = AbsolutePath(kwargs[strings.ABSOLUTE_PATH])
        self.container_format = kwargs[strings.CONTAINER_FORMAT]
        self.size = kwargs[strings.SIZE]
        self.duration = kwargs[strings.DURATION]
        self.width = kwargs[strings.WIDTH]
        self.height = kwargs[strings.HEIGHT]
        self.video_codec = kwargs[strings.VIDEO_CODEC]
        self.audio_codec = kwargs[strings.AUDIO_CODEC]
        self.frame_rate = kwargs[strings.FRAME_RATE]
        self.sample_rate = kwargs[strings.SAMPLE_RATE]
        self.video_id = kwargs.get(strings.VIDEO_ID, None)
        self.date_added_microseconds = default(kwargs, strings.DATE_ADDED_MICROSECONDS, timestamp_microseconds)
        self.date_modified = default(kwargs, strings.DATE_MODIFIED, self.__get_date_modified)
        self.thumbnail = kwargs.get(strings.THUMBNAIL, None)
        self.properties = properties
        self.updated = bool(updated)

        assert isinstance(self.container_format, str)
        assert isinstance(self.size, int)
        assert isinstance(self.duration, float)
        assert isinstance(self.width, int)
        assert isinstance(self.height, int)
        assert isinstance(self.video_codec, str)
        assert isinstance(self.audio_codec, str) or self.audio_codec is None
        assert isinstance(self.frame_rate, float) or self.frame_rate is None
        assert isinstance(self.sample_rate, float) or self.sample_rate is None
        assert isinstance(self.video_id, int)
        assert isinstance(self.date_added_microseconds, int)
        assert isinstance(self.date_modified, float)
        # TODO Check thumbnail.
        assert isinstance(self.properties, PropertyDict) or self.properties is None

    title = property(lambda self: self.absolute_path.title)
    characteristics = property(lambda self: tuple(getattr(self, prop_name) for prop_name in self.__PROPS))
    path = property(lambda self: str(self.absolute_path))

    def __get_date_modified(self):
        return self.absolute_path.get_date_modified()

    def set_properties(self, properties):
        assert isinstance(properties, (PropertyDict, type(None)))
        self.properties = properties

    def to_json_data(self):
        json_dict = {key: getattr(self, key) for key in self.__slots__}
        json_dict[strings.ABSOLUTE_PATH] = str(self.absolute_path)
        if self.properties is not None:
            json_dict[strings.PROPERTIES] = self.properties.to_json_data()
        return json_dict

    @classmethod
    def from_json_data(cls, json_data, property_type_set=None):
        json_properties = json_data.pop(strings.PROPERTIES, None)
        if json_properties is not None:
            json_data[strings.PROPERTIES] = PropertyDict.from_json_data(json_properties, property_type_set)
        return cls(**json_data)
