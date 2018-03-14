from datetime import datetime

VIDEO_SUPPORTED_EXTENSIONS = {"3g2", "3gp", "asf", "avi", "drc", "f4a", "f4b", "f4p", "f4v", "flv", "gifv", "m2v",
                              "m4p", "m4v", "mkv", "mng", "mov", "mp2", "mp4", "mpe", "mpeg", "mpg", "mpv", "mxf",
                              "nsv", "ogg", "ogv", "qt", "rm", "rmvb", "roq", "svi", "vob", "webm", "wmv", "yuv"}


def timestamp_microseconds():
    """ Return current timestamp with microsecond resolution. """
    current_time = datetime.now()
    epoch = datetime.utcfromtimestamp(0)
    delta = current_time - epoch
    return (delta.days * 24 * 60 * 60 + delta.seconds) * 1000000 + delta.microseconds


class strings(object):
    ABSOLUTE_PATH = 'absolute_path'
    ABSOLUTE_PATH_HASH = 'absolute_path_hash'
    FORMAT = 'format'
    SIZE = 'size'
    DURATION = 'duration'
    WIDTH = 'width'
    HEIGHT = 'height'
    VIDEO_CODEC = 'video_codec'
    AUDIO_CODEC = 'audio_codec'
    FRAME_RATE = 'frame_rate'
    SAMPLE_RATE = 'sample_rate'
    DATE_ADDED_MICROSECONDS = 'date_added_microseconds'
    video_basic_fields = {ABSOLUTE_PATH, ABSOLUTE_PATH_HASH, FORMAT, SIZE, DURATION, WIDTH, HEIGHT,
                          VIDEO_CODEC, AUDIO_CODEC, FRAME_RATE, SAMPLE_RATE, DATE_ADDED_MICROSECONDS}
