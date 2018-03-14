from pysaurus.utils import strings


class Video(object):
    __slots__ = strings.video_basic_fields

    def __init__(self, **kwargs):
        assert len(kwargs) == len(self.__slots__) and all(attribute in kwargs for attribute in self.__slots__)
        self.absolute_path = kwargs[strings.ABSOLUTE_PATH]
        self.absolute_path_hash = kwargs[strings.ABSOLUTE_PATH_HASH]
        self.format = kwargs[strings.FORMAT]
        self.size = kwargs[strings.SIZE]
        self.duration = kwargs[strings.DURATION]
        self.width = kwargs[strings.WIDTH]
        self.height = kwargs[strings.HEIGHT]
        self.video_codec = kwargs[strings.VIDEO_CODEC]
        self.audio_codec = kwargs[strings.AUDIO_CODEC]
        self.frame_rate = kwargs[strings.FRAME_RATE]
        self.sample_rate = kwargs[strings.SAMPLE_RATE]
        self.date_added_microseconds = kwargs[strings.DATE_ADDED_MICROSECONDS]
