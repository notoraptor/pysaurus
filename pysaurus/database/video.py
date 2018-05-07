from pysaurus.database.property import PropertyDict
from pysaurus.utils import duration
from pysaurus.utils import strings
from pysaurus.utils.absolute_path import AbsolutePath
from pysaurus.utils.common import timestamp_microseconds
from pysaurus.utils.json_compatible import JSONCompatible


class Video(JSONCompatible):
    __FILE_PROPS = (strings.ABSOLUTE_PATH, strings.VIDEO_ID, strings.DATE_ADDED_MICROSECONDS,
                    strings.THUMBNAIL, strings.DATE_MODIFIED, strings.MOVIE_TITLE,
                    strings.PROPERTIES, strings.UPDATED, 'suspect')
    __VIDEO_PROPS = tuple(sorted((
        strings.CONTAINER_FORMAT, strings.SIZE, strings.DURATION, strings.DURATION_UNIT, strings.WIDTH, strings.HEIGHT,
        strings.VIDEO_CODEC, strings.AUDIO_CODEC, strings.FRAME_RATE, strings.SAMPLE_RATE
    )))
    __slots__ = __FILE_PROPS + __VIDEO_PROPS

    def __init__(self):
        self.absolute_path = None  # type: AbsolutePath
        self.date_added_microseconds = None  # type: int
        self.date_modified = None  # type: float
        self.thumbnail = None  # type: AbsolutePath
        self.movie_title = None  # type: str
        self.video_id = None  # type: int
        self.container_format = None  # type: str
        self.size = None  # type: int
        self.duration = None  # type: int | float
        self.duration_unit = None  # type: str
        self.width = None  # type: int
        self.height = None  # type: int
        self.video_codec = None  # type: str
        self.audio_codec = None  # type: str
        self.frame_rate = None  # type: int | float
        self.sample_rate = None  # type: int | float
        self.properties = None  # type: PropertyDict
        self.updated = False
        self.suspect = None

    title = property(lambda self: self.movie_title or self.absolute_path.title)
    characteristics = property(lambda self: tuple(getattr(self, prop_name) for prop_name in self.__PROPS))
    duration_microseconds = property(
        lambda self: duration.Duration(self.duration, self.duration_unit).to_microseconds())

    def update(self, dictionary):
        """ Update video fields from a dictionary. Consider manually validate() video after updating.
        :param dictionary: dictionary with keys matching Video class attributes.
        :type dictionary: dict
        """
        for key in self.__slots__:
            setattr(self, key, dictionary.get(key, getattr(self, key)))

    def validate(self):
        self.absolute_path = AbsolutePath.ensure(self.absolute_path)
        if self.date_added_microseconds is None:
            self.date_added_microseconds = timestamp_microseconds()
        if self.date_modified is None:
            self.date_modified = self.absolute_path.get_date_modified()
        if self.thumbnail is not None:
            self.thumbnail = AbsolutePath.ensure(self.thumbnail)
        assert isinstance(self.video_id, int)
        assert isinstance(self.date_added_microseconds, int)
        assert isinstance(self.date_modified, float)
        assert isinstance(self.movie_title, (str, type(None)))
        assert isinstance(self.container_format, str)
        assert isinstance(self.size, int)
        assert isinstance(self.duration, (int, float))
        assert self.duration_unit in duration.TIME_UNITS
        assert isinstance(self.width, int), (type(self.width), self.width)
        assert isinstance(self.height, int)
        assert isinstance(self.video_codec, str)
        assert isinstance(self.frame_rate, (int, float))
        assert isinstance(self.audio_codec, (str, type(None)))
        assert isinstance(self.sample_rate, (int, float, type(None)))
        assert isinstance(self.properties, (PropertyDict, type(None)))
        assert self.suspect is None or isinstance(self.suspect, list)

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
            self.thumbnail = None
            self.updated = True

    def to_json_data(self):
        # Don't save attribute 'updated'.
        json_dict = {key: getattr(self, key) for key in self.__slots__}
        del json_dict['updated']
        json_dict[strings.ABSOLUTE_PATH] = str(self.absolute_path)
        json_dict[strings.THUMBNAIL] = str(self.thumbnail) if self.thumbnail else None
        if self.properties is not None:
            json_dict[strings.PROPERTIES] = self.properties.to_json_data()
        return json_dict

    @classmethod
    def from_json_data(cls, json_data, property_type_set=None):
        """ Load a Video object from given JSON dictionary and optional property set.
            :type json_data: dict
            :type property_type_set: pysaurus.database.property.PropertyTypeDict
            :rtype: Video
        """
        json_properties = json_data.get(strings.PROPERTIES, None)
        if json_properties is not None:
            json_data[strings.PROPERTIES] = PropertyDict.from_json_data(json_properties, property_type_set)
        elif property_type_set is not None:
            json_data[strings.PROPERTIES] = PropertyDict(property_type_set)
        else:
            del json_data[strings.PROPERTIES]
        video = cls()
        video.update(json_data)
        video.validate()
        return video
