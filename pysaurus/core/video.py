from pysaurus.core import utils
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.c_video import CVideo
from pysaurus.core.html_stripper import HTMLStripper
from pysaurus.core.utils import StringPrinter
from pysaurus.core.video_duration import VideoDuration
from pysaurus.core.video_size import VideoSize


class Video(object):
    # Currently 14 fields.
    __slots__ = ('filename', 'title', 'container_format', 'audio_codec', 'video_codec', 'width', 'height',
                 'frame_rate_num', 'frame_rate_den', 'sample_rate', 'duration', 'duration_time_base', 'size',
                 'bit_rate', 'thumbnail', 'warnings')

    MIN_TO_LONG = {
        'f': 'filename',
        'n': 'title',
        'c': 'container_format',
        'a': 'audio_codec',
        'v': 'video_codec',
        'w': 'width',
        'h': 'height',
        'x': 'frame_rate_num',
        'y': 'frame_rate_den',
        'u': 'sample_rate',
        'd': 'duration',
        't': 'duration_time_base',
        's': 'size',
        'r': 'bit_rate',
        'i': 'thumbnail',
        'e': 'warnings'
    }
    LONG_TO_MIN = {_long: _min for _min, _long in MIN_TO_LONG.items()}

    def __init__(self, data, database_folder: AbsolutePath = None):
        self.filename = None  # type: AbsolutePath
        self.title = ''
        self.container_format = ''
        self.audio_codec = ''
        self.video_codec = ''
        self.width = 0
        self.height = 0
        self.frame_rate_num = 0
        self.frame_rate_den = 0
        self.sample_rate = 0
        self.duration = 0
        self.duration_time_base = 0
        self.size = 0
        self.bit_rate = 0
        self.thumbnail = None  # type: AbsolutePath
        self.warnings = set()
        if data:
            if isinstance(data, CVideo):
                self.filename = AbsolutePath(data.filename.decode()) if data.filename else None
                self.title = data.title.decode() if data.title else None
                self.container_format = data.container_format.decode() if data.container_format else None
                self.audio_codec = data.audio_codec.decode() if data.audio_codec else None
                self.video_codec = data.video_codec.decode() if data.video_codec else None
                self.width = data.width
                self.height = data.height
                self.frame_rate_num = data.frame_rate_num
                self.frame_rate_den = data.frame_rate_den
                self.sample_rate = data.sample_rate
                self.duration = data.duration
                self.duration_time_base = data.duration_time_base
                self.size = data.size
                self.bit_rate = data.bit_rate
            elif isinstance(data, dict):
                for field_name in self.__slots__:
                    setattr(self, field_name, data[self.LONG_TO_MIN[field_name]])
                self.filename = AbsolutePath.ensure(self.filename)
                self.warnings = set(self.warnings)
                if self.thumbnail:
                    self.thumbnail = AbsolutePath.ensure(self.thumbnail)
                    if not self.thumbnail_is_valid() and database_folder and self.thumbnail.extension.lower() == utils.THUMBNAIL_EXTENSION:
                        alt_file_path = AbsolutePath.new_file_path(database_folder, self.thumbnail.title,
                                                                   self.thumbnail.extension)
                        if alt_file_path.exists() and alt_file_path.isfile():
                            self.thumbnail = alt_file_path
                    if not self.thumbnail_is_valid():
                        self.thumbnail = None
            else:
                raise Exception('Invalid video initialization data: %s' % data)
        if self.title:
            self.title = HTMLStripper.strip(self.title)
        else:
            self.title = ''

    def __str__(self):
        printer = StringPrinter()
        printer.write('Video(')
        for field_name in sorted(self.__slots__):
            printer.write('\t%s: %s' % (field_name, getattr(self, field_name)))
        printer.write(')')
        return str(printer)

    def file_exists(self):
        return self.filename.exists()

    def get_duration(self):
        return VideoDuration(self)

    def get_size(self):
        return VideoSize(self)

    def to_dict(self):
        dct = {self.LONG_TO_MIN[key]: getattr(self, key) for key in self.__slots__}
        dct[self.LONG_TO_MIN['filename']] = str(self.filename)
        dct[self.LONG_TO_MIN['thumbnail']] = str(self.thumbnail) if self.thumbnail else None
        return dct

    def thumbnail_is_valid(self):
        return (isinstance(self.thumbnail, AbsolutePath)
                and self.thumbnail.exists()
                and self.thumbnail.isfile()
                and self.thumbnail.extension.lower() == utils.THUMBNAIL_EXTENSION)

    def get_title(self):
        return HTMLStripper.strip(self.title) if self.title else self.filename.title
