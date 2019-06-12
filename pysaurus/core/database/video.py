from PIL import Image

from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.components.duration import Duration
from pysaurus.core.components.file_size import FileSize
from pysaurus.core.database import path_utils
from pysaurus.core.utils.classes import StringPrinter, HTMLStripper
from pysaurus.core.utils.constants import PYTHON_ERROR_THUMBNAIL
from pysaurus.core.video_clipping import video_clip_to_base64
from pysaurus.core.video_raptor.structures import VideoInfo

WORK_MODE = 'RGB'
import base64
from io import BytesIO
from pysaurus.core.utils.constants import THUMBNAIL_EXTENSION


class Video(object):
    # Currently 14 fields.
    __slots__ = ('filename', 'title', 'container_format', 'audio_codec', 'video_codec', 'width', 'height',
                 'frame_rate_num', 'frame_rate_den', 'sample_rate', 'duration', 'duration_time_base', 'size',
                 'bit_rate', 'thumb_name', 'errors', 'error_thumbnail')

    __fields__ = __slots__[:-1]

    MIN_TO_LONG = {'f': 'filename', 'n': 'title', 'c': 'container_format', 'a': 'audio_codec', 'v': 'video_codec',
                   'w': 'width', 'h': 'height', 'x': 'frame_rate_num', 'y': 'frame_rate_den', 'u': 'sample_rate',
                   'd': 'duration', 't': 'duration_time_base', 's': 'size', 'r': 'bit_rate',
                   'i': 'thumb_name', 'e': 'errors'}

    LONG_TO_MIN = {_long: _min for _min, _long in MIN_TO_LONG.items()}

    PUBLIC_INFO = (
        # Video class fields
        'filename', 'container_format', 'audio_codec', 'video_codec', 'width', 'height', 'sample_rate', 'bit_rate',
        # special fields
        'size', 'duration', 'microseconds', 'frame_rate', 'name', 'date', 'meta_title', 'file_title'
    )

    def __init__(self, filename, title='', container_format='', audio_codec='', video_codec='', width=0, height=0,
                 frame_rate_num=0, frame_rate_den=0, sample_rate=0, duration=0, duration_time_base=0, size=0,
                 bit_rate=0, thumb_name='', errors=()):
        self.filename = AbsolutePath.ensure(filename)
        self.title = HTMLStripper.strip(title) if title else ''
        self.container_format = container_format or ''
        self.audio_codec = audio_codec or ''
        self.video_codec = video_codec or ''
        self.width = width or 0
        self.height = height or 0
        self.frame_rate_num = frame_rate_num or 0
        self.frame_rate_den = frame_rate_den or 1
        self.sample_rate = sample_rate or 0
        self.duration = duration or 0
        self.duration_time_base = duration_time_base or 1
        self.size = size or 0
        self.bit_rate = bit_rate or 0
        self.thumb_name = thumb_name
        self.errors = set(errors)
        self.error_thumbnail = PYTHON_ERROR_THUMBNAIL in self.errors
        if self.error_thumbnail:
            self.errors.remove(PYTHON_ERROR_THUMBNAIL)

    def __str__(self):
        printer = StringPrinter()
        printer.write('Video:')
        for field_name in ('filename', 'title', 'container_format', 'audio_codec',
                           'video_codec', 'width', 'height', 'sample_rate', 'bit_rate'):
            printer.write('\t%s: %s' % (field_name, getattr(self, field_name)))
        printer.write('\tframe_rate: %s' % (self.frame_rate_num / self.frame_rate_den))
        printer.write('\tduration: %s' % (self.get_duration()))
        printer.write('\tsize: %s' % (self.get_size()))
        errors = set(self.errors)
        if self.error_thumbnail:
            errors.add(PYTHON_ERROR_THUMBNAIL)
        if errors:
            printer.write('\terror(s): %s' % (', '.join(sorted(errors))))
        return str(printer)

    def exists(self):
        return self.filename.isfile()

    def get_title(self):
        return self.title if self.title else self.filename.title

    def get_duration(self):
        """ Return a Duration object representing the video duration.
            Based on raw duration fields `duration` and `duration_time_base`, we have:
                duration = (number of seconds) * duration_time_base
            So
                (number of seconds) = duration / duration_time_base
        """
        return Duration(round(self.duration * 1000000 / self.duration_time_base))

    def get_size(self):
        return FileSize(self.size)

    def thumbnail_is_valid(self, folder: AbsolutePath):
        return self.get_thumbnail_path(folder).isfile()

    def ensure_thumbnail_name(self):
        if not self.thumb_name:
            self.thumb_name = path_utils.generate_thumb_name(self.filename)
        return self.thumb_name

    def get_thumbnail_path(self, folder: AbsolutePath):
        return path_utils.generate_thumb_path(folder, self.ensure_thumbnail_name())

    def get(self, field):
        if field == 'size':
            return self.get_size()
        if field == 'duration':
            return self.get_duration()
        if field == 'microseconds':
            return self.get_duration().total_microseconds
        if field == 'frame_rate':
            return self.frame_rate_num / self.frame_rate_den
        if field == 'name':
            return self.get_title()
        if field == 'meta_title':
            return self.title
        if field == 'file_title':
            return self.filename.title
        if field == 'date':
            return self.filename.get_date_modified()
        if field in self.PUBLIC_INFO:
            return getattr(self, field)
        return None

    def info(self, **extra):
        info = {public_field: self.get(public_field) for public_field in self.PUBLIC_INFO}
        info.update(extra)
        return info

    def thumbnail_to_base64(self, thumb_folder: AbsolutePath):
        thumb_path = self.get_thumbnail_path(thumb_folder)
        if not thumb_path.isfile():
            return None
        image = Image.open(thumb_path.path)
        if image.mode != WORK_MODE:
            image = image.convert(WORK_MODE)
        buffered = BytesIO()
        image.save(buffered, format=THUMBNAIL_EXTENSION)
        image_string = base64.b64encode(buffered.getvalue())
        return image_string

    def clip_to_base64(self, index, length):
        return video_clip_to_base64(
            path=self.filename.path,
            clip_index=index,
            clip_seconds=length,
            unique_id=self.ensure_thumbnail_name()
        )

    def to_dict(self):
        dct = {self.LONG_TO_MIN[key]: getattr(self, key) for key in self.__fields__}
        dct[self.LONG_TO_MIN['filename']] = str(self.filename)
        if self.error_thumbnail:
            dct[self.LONG_TO_MIN['errors']].add(PYTHON_ERROR_THUMBNAIL)
        return dct

    @classmethod
    def from_dict(cls, dct: dict):
        return cls(**{field: dct[cls.LONG_TO_MIN[field]] for field in cls.__fields__})

    @classmethod
    def from_video_info(cls, video_info: VideoInfo):
        return cls(filename=(AbsolutePath(video_info.filename.decode()) if video_info.filename else None),
                   title=(video_info.title.decode() if video_info.title else None),
                   container_format=(video_info.container_format.decode() if video_info.container_format else None),
                   audio_codec=(video_info.audio_codec.decode() if video_info.audio_codec else None),
                   video_codec=(video_info.video_codec.decode() if video_info.video_codec else None),
                   width=video_info.width,
                   height=video_info.height,
                   frame_rate_num=video_info.frame_rate_num,
                   frame_rate_den=video_info.frame_rate_den,
                   sample_rate=video_info.sample_rate,
                   duration=video_info.duration,
                   duration_time_base=video_info.duration_time_base,
                   size=video_info.size,
                   bit_rate=video_info.bit_rate)
