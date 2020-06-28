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

from pysaurus.core.classes import StringPrinter
from pysaurus.core.components import AbsolutePath, Duration
from pysaurus.core.constants import THUMBNAIL_EXTENSION
from pysaurus.core.database import path_utils
from pysaurus.core.database.video_state import VideoState
from pysaurus.core.functions import html_to_title, string_to_pieces
from pysaurus.core.modules import VideoClipping, ImageUtils


class Video(VideoState):
    UNREADABLE = False

    __slots__ = (
        # Video properties
        'audio_bit_rate',
        'audio_codec',
        'audio_codec_description',
        'container_format',
        'device_name',  # private field
        'duration',
        'duration_time_base',
        'frame_rate_den',
        'frame_rate_num',
        'height',
        'meta_title',
        'sample_rate',
        'thumb_name',
        'video_codec',
        'video_codec_description',
        'width',
        # Runtime attributes
        'runtime_has_thumbnail',
    )

    QUALITY_FIELDS = (
        ('height', 5),
        ('width', 4),
        ('raw_seconds', 3),
        ('frame_rate', 2),
        ('file_size', 1),
        ('audio_bit_rate', 1),
    )

    @property
    def quality(self):
        total_level = 0
        qualities = {}
        for field, level in self.QUALITY_FIELDS:
            value = getattr(self, field)
            min_value = self.database.video_property_bound.min[field]
            max_value = self.database.video_property_bound.max[field]
            if min_value == max_value:
                assert value == min_value, (value, min_value)
                quality = 0
            else:
                quality = (value - min_value) / (max_value - min_value)
                assert 0 <= quality <= 1, (quality, field, value, min_value, max_value)
            qualities[field] = quality * level
            total_level += level
        return sum(qualities.values()) * 100 / total_level

    MIN_TO_LONG = {
        'r': 'audio_bit_rate',
        'a': 'audio_codec',
        'A': 'audio_codec_description',
        'c': 'container_format',
        'b': 'device_name',
        'd': 'duration',
        't': 'duration_time_base',
        'y': 'frame_rate_den',
        'x': 'frame_rate_num',
        'h': 'height',
        'n': 'meta_title',
        'u': 'sample_rate',
        'i': 'thumb_name',
        'v': 'video_codec',
        'V': 'video_codec_description',
        'w': 'width',
    }

    LONG_TO_MIN = {_long: _min for _min, _long in MIN_TO_LONG.items()}

    ROW_ATTRIBUTES = (
        'audio_bit_rate',
        'audio_codec',
        'audio_codec_description',
        'container_format',
        'errors',  # from VideoState
        'filename',  # from VideoState
        'height',
        'meta_title',
        'sample_rate',
        'video_codec',
        'video_codec_description',
        'width',
    )

    ROW_PROPERTIES = (
        'date',  # property VideoState.date
        'extension',  # from VideoState.filename
        'file_title',  # from VideoState.filename
        'frame_rate',  # frame_rate_num, frame_rate_den
        'length',  # duration, duration_time_base
        'size',  # property VideoState.size
        'thumbnail_path',  # thumb_name
        'title',  # meta_title, file_title
        'quality',  # SPECIAL
    )

    ROW_FIELDS = ROW_ATTRIBUTES + ROW_PROPERTIES

    def __init__(self,
                 # Runtime arguments
                 database, from_dictionary=None,
                 # VideoState optional arguments
                 filename=None, size=0, errors=(), video_id=None,
                 # Video optional arguments
                 audio_bit_rate=0, audio_codec='', audio_codec_description='', container_format='', device_name='',
                 duration=0, duration_time_base=0, frame_rate_den=0, frame_rate_num=0, height=0, meta_title='',
                 sample_rate=0, thumb_name='', video_codec='', video_codec_description='', width=0):
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
            audio_bit_rate = from_dictionary.get(self.LONG_TO_MIN['audio_bit_rate'], audio_bit_rate)
            audio_codec = from_dictionary.get(self.LONG_TO_MIN['audio_codec'], audio_codec)
            audio_codec_description = from_dictionary.get(self.LONG_TO_MIN['audio_codec_description'],
                                                          audio_codec_description)
            container_format = from_dictionary.get(self.LONG_TO_MIN['container_format'], container_format)
            device_name = from_dictionary.get(self.LONG_TO_MIN['device_name'], device_name)
            duration = from_dictionary.get(self.LONG_TO_MIN['duration'], duration)
            duration_time_base = from_dictionary.get(self.LONG_TO_MIN['duration_time_base'], duration_time_base)
            frame_rate_den = from_dictionary.get(self.LONG_TO_MIN['frame_rate_den'], frame_rate_den)
            frame_rate_num = from_dictionary.get(self.LONG_TO_MIN['frame_rate_num'], frame_rate_num)
            height = from_dictionary.get(self.LONG_TO_MIN['height'], height)
            meta_title = from_dictionary.get(self.LONG_TO_MIN['meta_title'], meta_title)
            sample_rate = from_dictionary.get(self.LONG_TO_MIN['sample_rate'], sample_rate)
            thumb_name = from_dictionary.get(self.LONG_TO_MIN['thumb_name'], thumb_name)
            video_codec = from_dictionary.get(self.LONG_TO_MIN['video_codec'], video_codec)
            video_codec_description = from_dictionary.get(self.LONG_TO_MIN['video_codec_description'],
                                                          video_codec_description)
            width = from_dictionary.get(self.LONG_TO_MIN['width'], width)
        super(Video, self).__init__(filename=filename, size=size, errors=errors, video_id=video_id,
                                    database=database, from_dictionary=from_dictionary)
        self.audio_bit_rate = audio_bit_rate
        self.audio_codec = audio_codec
        self.audio_codec_description = audio_codec_description
        self.container_format = container_format
        self.device_name = device_name
        self.duration = duration
        self.duration_time_base = duration_time_base or 1
        self.frame_rate_den = frame_rate_den or 1
        self.frame_rate_num = frame_rate_num
        self.height = height
        self.meta_title = html_to_title(meta_title)
        self.sample_rate = sample_rate
        self.thumb_name = thumb_name
        self.video_codec = video_codec
        self.video_codec_description = video_codec_description
        self.width = width

        self.runtime_has_thumbnail = False

    def __str__(self):
        with StringPrinter() as printer:
            printer.write('Video %s:' % self.video_id)
            for field in self.ROW_FIELDS:
                printer.write('\t%s: %s' % (field, getattr(self, field)))
            return str(printer)

    extension = property(lambda self: self.filename.extension)
    file_title = property(lambda self: self.filename.title)
    frame_rate = property(lambda self: self.frame_rate_num / self.frame_rate_den)
    length = property(lambda self: Duration(round(self.duration * 1000000 / self.duration_time_base)))
    title = property(lambda self: self.meta_title if self.meta_title else self.filename.title)

    raw_seconds = property(lambda self: self.duration / self.duration_time_base)
    raw_microseconds = property(lambda self: self.duration * 1000000 / self.duration_time_base)

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
    def compare(self, other, sorting):
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

    META_FIELDS = (
        'audio_bit_rate',
        'audio_codec',
        'audio_codec_description',
        'container_format',
        'duration',
        'duration_time_base',
        'file_size',
        'frame_rate_den',
        'frame_rate_num',
        'height',
        'meta_title',
        'sample_rate',
        'video_codec',
        'video_codec_description',
        'width',
    )

    def meta(self):
        return tuple(getattr(self, field) for field in self.META_FIELDS)
