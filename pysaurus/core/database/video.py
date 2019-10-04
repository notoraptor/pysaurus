"""
Video class. Properties:

- length: Return a Duration object representing the video duration.
  Based on raw duration fields `duration` and `duration_time_base`, we have: ::

    duration = (number of seconds) * duration_time_base

  So: ::

    (number of seconds) = duration / duration_time_base


"""

import base64
from io import BytesIO

from PIL import Image

from pysaurus.core.classes import StringPrinter
from pysaurus.core.components import AbsolutePath, Duration
from pysaurus.core.constants import THUMBNAIL_EXTENSION
from pysaurus.core.database import path_utils
from pysaurus.core.database.video_state import VideoState
from pysaurus.core.modules import HTMLStripper, VideoClipping

WORK_MODE = 'RGB'


class Video(VideoState):

    # Currently 14 fields.
    __slots__ = ('meta_title', 'container_format', 'width', 'height',
                 'audio_codec', 'video_codec', 'audio_codec_description', 'video_codec_description',
                 'frame_rate_num', 'frame_rate_den', 'sample_rate', 'duration', 'duration_time_base',
                 'audio_bit_rate', 'thumb_name', 'database')

    ROW_FIELDS = (
        # basic fields
        'filename', 'container_format', 'width', 'height',
        'audio_codec', 'video_codec', 'audio_codec_description', 'video_codec_description',
        'sample_rate', 'audio_bit_rate', 'errors',
        # special fields
        'frame_rate', 'length', 'size', 'date', 'title', 'meta_title', 'file_title', 'extension')

    def to_row(self):
        return [getattr(self, field) for field in self.ROW_FIELDS]

    def get(self, field):
        return getattr(self, field)

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
        """ Constructor.
        :type database: pysaurus.core.database.database.Database
        """
        super(Video, self).__init__(
            AbsolutePath.ensure(filename),
            size or 0,
            False,
            errors,
            video_id if isinstance(video_id, int) else None)
        self.database = database
        self.meta_title = ''
        if title:
            self.meta_title = HTMLStripper.strip(title)
            strip_again = True
            while strip_again:
                strip_again = False
                for character in ('"', "'"):
                    if self.meta_title.startswith(character) and self.meta_title.endswith(character):
                        self.meta_title = self.meta_title.strip(character)
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

    def __str__(self):
        with StringPrinter() as printer:
            printer.write('Video:')
            for field_name in ('video_id', 'filename', 'title', 'container_format',
                               'audio_codec', 'video_codec', 'audio_codec_description', 'video_codec_description',
                               'width', 'height', 'sample_rate', 'audio_bit_rate'):
                printer.write('\t%s: %s' % (field_name, getattr(self, field_name)))
            printer.write('\tframe_rate: %s' % self.frame_rate)
            printer.write('\tduration: %s' % self.length)
            printer.write('\tsize: %s' % self.size)
            if self.errors:
                printer.write('\terror(s): %s' % (', '.join(sorted(self.errors))))
            return str(printer)

    title = property(lambda self: self.meta_title if self.meta_title else self.filename.title)
    frame_rate = property(lambda self: self.frame_rate_num / self.frame_rate_den)
    date = property(lambda self: self.filename.get_date_modified())
    file_title = property(lambda self: self.filename.title)
    extension = property(lambda self: self.filename.extension)
    length = property(lambda self: Duration(round(self.duration * 1000000 / self.duration_time_base)))

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
        return VideoClipping.video_clip_to_base64(
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
