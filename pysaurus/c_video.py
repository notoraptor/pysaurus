from ctypes import Structure, c_char_p, c_int, c_int64


class CVideo(Structure):
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
        ("bit_rate", c_int64)
    ]
