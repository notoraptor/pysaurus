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
from pysaurus.core.functions import html_to_title, string_to_pieces
from pysaurus.core.modules import VideoClipping, ImageUtils


class Video(VideoState):
    UNREADABLE = False

    # Currently 14 fields.
    __slots__ = ('meta_title', 'container_format',
                 'audio_codec', 'video_codec', 'audio_codec_description', 'video_codec_description',
                 'width', 'height', 'frame_rate_num', 'frame_rate_den', 'sample_rate', 'runtime_has_thumbnail',
                 'duration', 'duration_time_base', 'audio_bit_rate', 'thumb_name', 'device_name')

    MIN_TO_LONG = {'n': 'meta_title', 'c': 'container_format', 'a': 'audio_codec', 'v': 'video_codec',
                   'A': 'audio_codec_description', 'V': 'video_codec_description',
                   'w': 'width', 'h': 'height', 'x': 'frame_rate_num', 'y': 'frame_rate_den', 'u': 'sample_rate',
                   'd': 'duration', 't': 'duration_time_base', 'r': 'audio_bit_rate', 'i': 'thumb_name',
                   'b': 'device_name'}

    LONG_TO_MIN = {_long: _min for _min, _long in MIN_TO_LONG.items()}

    ROW_FIELDS = (
        # basic fields
        'filename', 'errors', 'meta_title', 'container_format',
        'audio_codec', 'video_codec', 'audio_codec_description', 'video_codec_description',
        'width', 'height', 'sample_rate', 'audio_bit_rate',
        # special fields
        'frame_rate', 'length', 'size', 'date', 'title', 'file_title', 'extension', 'thumbnail_path')

    def __init__(self, database, filename=None, size=0, errors=(), video_id=None,
                 meta_title='', container_format='', audio_codec='', video_codec='',
                 audio_codec_description='', video_codec_description='', width=0, height=0,
                 frame_rate_num=0, frame_rate_den=0, sample_rate=0, duration=0, duration_time_base=0,
                 audio_bit_rate=0, thumb_name='', device_name='', from_dictionary=None):
        """
        :type filename: AbsolutePath | str
        :type database: pysaurus.core.database.database.Database
        :type size: int
        :type errors: set
        :type video_id: int, optional
        :type meta_title: str
        :type container_format: str
        :type audio_codec: str
        :type video_codec: str
        :type audio_codec_description: str
        :type video_codec_description: str
        :type width: int
        :type height: int
        :type frame_rate_num: int
        :type frame_rate_den: int
        :type sample_rate: float
        :type duration: int
        :type duration_time_base: int
        :type audio_bit_rate: int
        :type thumb_name: str
        :type device_name: str
        :type from_dictionary: dict
        """
        if from_dictionary:
            meta_title = from_dictionary.get(self.LONG_TO_MIN['meta_title'], meta_title)
            container_format = from_dictionary.get(self.LONG_TO_MIN['container_format'], container_format)
            audio_codec = from_dictionary.get(self.LONG_TO_MIN['audio_codec'], audio_codec)
            video_codec = from_dictionary.get(self.LONG_TO_MIN['video_codec'], video_codec)
            audio_codec_description = from_dictionary.get(self.LONG_TO_MIN['audio_codec_description'],
                                                          audio_codec_description)
            video_codec_description = from_dictionary.get(self.LONG_TO_MIN['video_codec_description'],
                                                          video_codec_description)
            width = from_dictionary.get(self.LONG_TO_MIN['width'], width)
            height = from_dictionary.get(self.LONG_TO_MIN['height'], height)
            frame_rate_num = from_dictionary.get(self.LONG_TO_MIN['frame_rate_num'], frame_rate_num)
            frame_rate_den = from_dictionary.get(self.LONG_TO_MIN['frame_rate_den'], frame_rate_den)
            sample_rate = from_dictionary.get(self.LONG_TO_MIN['sample_rate'], sample_rate)
            duration = from_dictionary.get(self.LONG_TO_MIN['duration'], duration)
            duration_time_base = from_dictionary.get(self.LONG_TO_MIN['duration_time_base'], duration_time_base)
            audio_bit_rate = from_dictionary.get(self.LONG_TO_MIN['audio_bit_rate'], audio_bit_rate)
            thumb_name = from_dictionary.get(self.LONG_TO_MIN['thumb_name'], thumb_name)
            device_name = from_dictionary.get(self.LONG_TO_MIN['device_name'], device_name)
        super(Video, self).__init__(filename=filename, size=size, errors=errors, video_id=video_id, database=database,
                                    from_dictionary=from_dictionary)
        self.meta_title = html_to_title(meta_title)
        self.container_format = container_format
        self.audio_codec = audio_codec
        self.video_codec = video_codec
        self.audio_codec_description = audio_codec_description
        self.video_codec_description = video_codec_description
        self.width = width
        self.height = height
        self.frame_rate_num = frame_rate_num
        self.frame_rate_den = frame_rate_den or 1
        self.sample_rate = sample_rate
        self.duration = duration
        self.duration_time_base = duration_time_base or 1
        self.audio_bit_rate = audio_bit_rate
        self.thumb_name = thumb_name
        self.device_name = device_name
        self.runtime_has_thumbnail = False

    def to_row(self):
        return [getattr(self, field) for field in self.ROW_FIELDS]

    def get(self, field):
        return getattr(self, field)

    def __str__(self):
        with StringPrinter() as printer:
            printer.write('Video %s:' % self.video_id)
            for field in self.ROW_FIELDS:
                printer.write('\t%s: %s' % (field, getattr(self, field)))
            return str(printer)

    title = property(lambda self: self.meta_title if self.meta_title else self.filename.title)
    frame_rate = property(lambda self: self.frame_rate_num / self.frame_rate_den)
    date = property(lambda self: self.runtime_date)
    file_title = property(lambda self: self.filename.title)
    extension = property(lambda self: self.filename.extension)
    length = property(lambda self: Duration(round(self.duration * 1000000 / self.duration_time_base)))

    @property
    def thumbnail_path(self):
        return path_utils.generate_thumb_path(self.database.thumbnail_folder, self.ensure_thumbnail_name())

    def ensure_thumbnail_name(self):
        if not self.thumb_name:
            self.thumb_name = path_utils.generate_thumb_name(self.filename)
            if self.database.system_is_case_insensitive:
                self.thumb_name = self.thumb_name.lower()
        return self.thumb_name

    def thumbnail_is_valid(self):
        return not self.error_thumbnail and self.runtime_has_thumbnail

    def thumbnail_to_base64(self):
        thumb_path = self.thumbnail_path
        if not thumb_path.isfile():
            return None
        image = ImageUtils.open_rgb_image(thumb_path.path)
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

    def terms(self, as_set=False):
        return string_to_pieces(' '.join((
            self.filename.path,
            self.meta_title,
            self.container_format,
            self.audio_codec,
            self.audio_codec_description,
            self.video_codec,
            self.video_codec_description,
            str(self.width),
            str(self.height),
            str(self.sample_rate),
        )), as_set=as_set)

    def to_dict(self):
        dct = super().to_dict()
        len_before = len(dct)
        for _min, _long in self.MIN_TO_LONG.items():
            assert _min not in dct, (_min, _long)
            dct[_min] = getattr(self, _long)
        assert len(dct) == len_before + len(self.MIN_TO_LONG)
        return dct

    @classmethod
    def from_dict(cls, dct, database):
        """
        :type dct: dict
        :type database: pysaurus.core.database.database.Database
        :rtype: Video
        """
        return cls(database=database, from_dictionary=dct)

    @staticmethod
    def compare_to(self, other, sorting):
        # type: (Video, Video, list) -> int
        for sort in sorting:
            reverse = sort[0] == '-'
            field = sort[1:]
            f1 = getattr(self, field)
            f2 = getattr(other, field)
            ret = 0
            if f1 < f2:
                ret = -1
            elif f1 > f2:
                ret = 1
            if ret:
                return -ret if reverse else ret
        return 0
