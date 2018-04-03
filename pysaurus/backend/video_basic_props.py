class VideoBasicProps(object):
    __slots__ = ('container_format', 'size', 'duration', 'duration_unit',
                 'width', 'height', 'video_codec', 'frame_rate', 'audio_codec', 'sample_rate')

    def __init__(self):
        self.duration = None
        self.duration_unit = None
        self.size = None
        self.container_format = None
        self.width = None
        self.height = None
        self.video_codec = None
        self.frame_rate = None

        self.audio_codec = None
        self.sample_rate = None

    def to_dict(self):
        return {name: getattr(self, name) for name in self.__slots__}
