from _ctypes import Structure
from ctypes import c_size_t, c_char_p, c_uint, c_char, c_int, c_int64

ERROR_DETAIL_MAX_LENGTH = 64


class VideoRaptorInfo(Structure):
    _fields_ = [
        ('hardwareDevicesCount', c_size_t),
        ('hardwareDevicesNames', c_char_p)
    ]


class ErrorReader(Structure):
    _fields_ = [
        ('errors', c_uint),
        ('position', c_uint),
    ]


class VideoReport(Structure):
    _fields_ = [
        ('errors', c_uint),
        ('errorDetail', c_char * ERROR_DETAIL_MAX_LENGTH)
    ]


class VideoInfo(Structure):
    _fields_ = [
        ("filename", c_char_p),
        ("title", c_char_p),
        ("container_format", c_char_p),
        ("audio_codec", c_char_p),
        ("video_codec", c_char_p),
        ("width", c_int),
        ("height", c_int),
        ("frame_rate_num", c_int),
        ("frame_rate_den", c_int),
        ("sample_rate", c_int),
        ("duration", c_int64),
        ("duration_time_base", c_int64),
        ("size", c_int64),
        ("bit_rate", c_int64),
        ("report", VideoReport)
    ]


class VideoThumbnail(Structure):
    _fields_ = [
        ("filename", c_char_p),
        ("thumbnailFolder", c_char_p),
        ("thumbnailName", c_char_p),
        ("report", VideoReport)
    ]
