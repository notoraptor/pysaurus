from pyraptor.c_video import CVideo
from pyraptor.utils import StringPrinter
from pyraptor.absolute_path import AbsolutePath

THUMBNAIL_EXTENSION = 'png'


class Video(object):
    # Currently 14 fields.
    __slots__ = ('filename', 'title', 'container_format', 'audio_codec', 'video_codec', 'width', 'height',
                 'frame_rate_num', 'frame_rate_den', 'sample_rate', 'duration', 'duration_time_base', 'size',
                 'bit_rate', 'thumbnail', 'warnings')

    def __init__(self, c_video):
        if c_video:
            if isinstance(c_video, CVideo):
                self.filename = AbsolutePath(c_video.filename.decode()) if c_video.filename else None
                self.title = c_video.title.decode() if c_video.title else None
                self.container_format = c_video.container_format.decode() if c_video.container_format else None
                self.audio_codec = c_video.audio_codec.decode() if c_video.audio_codec else None
                self.video_codec = c_video.video_codec.decode() if c_video.video_codec else None
                self.width = c_video.width
                self.height = c_video.height
                self.frame_rate_num = c_video.frame_rate_num
                self.frame_rate_den = c_video.frame_rate_den
                self.sample_rate = c_video.sample_rate
                self.duration = c_video.duration
                self.duration_time_base = c_video.duration_time_base
                self.size = c_video.size
                self.bit_rate = c_video.bit_rate
                self.warnings = set()
                self.thumbnail = None
            elif isinstance(c_video, dict):
                for field_name in self.__slots__:
                    setattr(self, field_name, c_video[field_name])
                self.filename = AbsolutePath.ensure(self.filename)
                self.warnings = set(self.warnings)
                if self.thumbnail:
                    self.thumbnail = AbsolutePath.ensure(self.thumbnail)
                    if not self.thumbnail_is_valid():
                        self.thumbnail = None
            else:
                raise Exception('Invalid given video initializer: %s' % c_video)
        else:
            self.filename = None
            self.title = None
            self.container_format = None
            self.audio_codec = None
            self.video_codec = None
            self.width = 0
            self.height = 0
            self.frame_rate_num = 0
            self.frame_rate_den = 0
            self.sample_rate = 0
            self.duration = 0
            self.duration = 0
            self.size = 0
            self.bit_rate = 0
            self.warnings = set()
            self.thumbnail = None

    def __str__(self):
        printer = StringPrinter()
        printer.write('Video(')
        for field_name in sorted(self.__slots__):
            printer.write('\t%s: %s' % (field_name, getattr(self, field_name)))
        printer.write(')')
        return str(printer)

    file_exists = property(lambda self: self.filename.exists())

    def to_dict(self):
        dct = {key: getattr(self, key) for key in self.__slots__}
        dct['filename'] = str(self.filename)
        dct['thumbnail'] = str(self.thumbnail) if self.thumbnail else None
        return dct

    def thumbnail_is_valid(self):
        return (
            isinstance(self.thumbnail, AbsolutePath)
            and self.thumbnail.exists()
            and self.thumbnail.isfile()
            and self.thumbnail.extension.lower() == THUMBNAIL_EXTENSION
        )

    def get_title(self) -> str:
        return self.title or self.filename.title
