import base64
from io import BytesIO

from PIL import Image

from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.components.duration import Duration
from pysaurus.core.components.file_size import FileSize
from pysaurus.core.database import path_utils
from pysaurus.core.database.video_state import VideoState
from pysaurus.core.utils.classes import HTMLStripper, StringPrinter
from pysaurus.core.utils.constants import PYTHON_ERROR_THUMBNAIL, THUMBNAIL_EXTENSION
from pysaurus.core.video_clipping import video_clip_to_base64

WORK_MODE = 'RGB'


class Video(VideoState):
    # Currently 14 fields.
    __slots__ = ('title', 'container_format', 'width', 'height',
                 'audio_codec', 'video_codec', 'audio_codec_description', 'video_codec_description',
                 'frame_rate_num', 'frame_rate_den', 'sample_rate', 'duration', 'duration_time_base',
                 'audio_bit_rate', 'thumb_name', 'video_id', 'database')

    TABLE_FIELDS = (
        # basic fields
        'filename', 'container_format', 'width', 'height',
        'audio_codec', 'video_codec', 'audio_codec_description', 'video_codec_description',
        'sample_rate', 'audio_bit_rate', 'errors',
        # special fields
        'frame_rate', 'duration_string', 'duration_value', 'size_string', 'size_value', 'date_string', 'date_value',
        'meta_title', 'file_title', 'extension')

    def to_table_line(self):
        duration = self.get_duration()
        date_modified = self.filename.get_date_modified()
        return [
            # basic fields
            self.filename.path,
            self.container_format,
            self.width,
            self.height,
            self.audio_codec,
            self.video_codec,
            self.audio_codec_description,
            self.video_codec_description,
            self.sample_rate,
            self.audio_bit_rate,
            self.errors,
            # special fields
            self.frame_rate_num / self.frame_rate_den,
            str(duration),
            duration.total_microseconds,
            str(self.get_size()),
            self.size,
            str(date_modified),
            date_modified.time,
            self.title,
            self.filename.title,
            self.filename.extension
        ]

    def get(self, field):
        return self.to_table_line()[self.TABLE_FIELDS.index(field)]

    def info(self, **extra):
        info = {field: value for (field, value) in zip(self.TABLE_FIELDS, self.to_table_line())}
        info.update(extra)
        return info

    MIN_TO_LONG = {'f': 'filename', 'n': 'title', 'c': 'container_format', 'a': 'audio_codec', 'v': 'video_codec',
                   'A': 'audio_codec_description', 'V': 'video_codec_description',
                   'w': 'width', 'h': 'height', 'x': 'frame_rate_num', 'y': 'frame_rate_den', 'u': 'sample_rate',
                   'd': 'duration', 't': 'duration_time_base', 's': 'size', 'r': 'audio_bit_rate',
                   'i': 'thumb_name', 'e': 'errors', 'j': 'video_id'}

    LONG_TO_MIN = {_long: _min for _min, _long in MIN_TO_LONG.items()}

    def __init__(self, filename, database, title='', container_format='', audio_codec='', video_codec='',
                 audio_codec_description='', video_codec_description='', width=0, height=0,
                 frame_rate_num=0, frame_rate_den=0, sample_rate=0, duration=0, duration_time_base=0, size=0,
                 audio_bit_rate=0, thumb_name='', errors=(), video_id=None):
        super(Video, self).__init__(AbsolutePath.ensure(filename), size or 0, False, errors)
        from pysaurus.core.database.database import Database
        self.database = database  # type: Database
        self.title = ''
        if title:
            self.title = HTMLStripper.strip(title)
            strip_again = True
            while strip_again:
                strip_again = False
                for character in ('"', "'"):
                    if self.title.startswith(character) and self.title.endswith(character):
                        self.title = self.title.strip(character)
                        strip_again = True
        self.container_format = container_format or ''
        self.audio_codec = audio_codec or ''
        self.video_codec = video_codec or ''
        self.audio_codec_description = audio_codec_description or ''
        self.video_codec_description = video_codec_description or ''
        self.width = width or 0
        self.height = height or 0
        self.frame_rate_num = frame_rate_num or 0
        self.frame_rate_den = frame_rate_den or 1
        self.sample_rate = sample_rate or 0
        self.duration = duration or 0
        self.duration_time_base = duration_time_base or 1
        self.audio_bit_rate = audio_bit_rate or 0
        self.thumb_name = thumb_name
        self.video_id = video_id if isinstance(video_id, int) else None

    def __str__(self):
        printer = StringPrinter()
        printer.write('Video:')
        for field_name in ('video_id', 'filename', 'title', 'container_format',
                           'audio_codec', 'video_codec', 'audio_codec_description', 'video_codec_description',
                           'width', 'height', 'sample_rate', 'audio_bit_rate'):
            printer.write('\t%s: %s' % (field_name, getattr(self, field_name)))
        printer.write('\tframe_rate: %s' % (self.frame_rate_num / self.frame_rate_den))
        printer.write('\tduration: %s' % (self.get_duration()))
        printer.write('\tsize: %s' % (self.get_size()))
        if self.errors:
            printer.write('\terror(s): %s' % (', '.join(sorted(self.errors))))
        return str(printer)

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

    def get_thumbnail_path(self):
        return path_utils.generate_thumb_path(self.database.folder, self.ensure_thumbnail_name())

    def ensure_thumbnail_name(self):
        if not self.thumb_name:
            self.thumb_name = path_utils.generate_thumb_name(self.filename)
            if self.database.system_is_case_insensitive:
                self.thumb_name = self.thumb_name.lower()
        return self.thumb_name

    def thumbnail_is_valid(self):
        return not self.error_thumbnail and self.get_thumbnail_path().isfile()

    def thumbnail_to_base64(self):
        thumb_path = self.get_thumbnail_path()
        if not thumb_path.isfile():
            return None
        image = Image.open(thumb_path.path)
        if image.mode != WORK_MODE:
            image = image.convert(WORK_MODE)
        buffered = BytesIO()
        image.save(buffered, format=THUMBNAIL_EXTENSION)
        image_string = base64.b64encode(buffered.getvalue())
        return image_string

    def clip_to_base64(self, start, length):
        return video_clip_to_base64(
            path=self.filename.path,
            time_start=start,
            clip_seconds=length,
            unique_id=self.ensure_thumbnail_name()
        )

    def to_dict(self):
        dct = {_min: getattr(self, _long) for (_min, _long) in self.MIN_TO_LONG.items()}
        dct[self.LONG_TO_MIN['filename']] = str(self.filename)
        return dct

    @classmethod
    def from_dict(cls, dct, database):
        return cls(database=database, **{_long: dct[_min] for (_min, _long) in cls.MIN_TO_LONG.items()})
