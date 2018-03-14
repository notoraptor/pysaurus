import os
import subprocess
import ujson as json
from datetime import datetime

import ffmpy
import whirlpool

VIDEO_SUPPORTED_EXTENSIONS = {"3g2", "3gp", "asf", "avi", "drc", "f4a", "f4b", "f4p", "f4v", "flv", "gifv", "m2v",
                              "m4p", "m4v", "mkv", "mng", "mov", "mp2", "mp4", "mpe", "mpeg", "mpg", "mpv", "mxf",
                              "nsv", "ogg", "ogv", "qt", "rm", "rmvb", "roq", "svi", "vob", "webm", "wmv", "yuv"}


def timestamp_microseconds():
    """ Return current timestamp with microsecond resolution.
        :return: int
    """
    current_time = datetime.now()
    epoch = datetime.utcfromtimestamp(0)
    delta = current_time - epoch
    return (delta.days * 24 * 60 * 60 + delta.seconds) * 1000000 + delta.microseconds


def _get_ffprobe_json_infos(video_absolute_file_path):
    ffprobe = ffmpy.FFprobe(
        global_options='-v quiet -print_format json -show_error -show_format -show_streams',
        inputs={video_absolute_file_path: None}
    )
    std_out, std_err = ffprobe.run(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if std_err:
        raise Exception(std_err)
    return json.loads(std_out)


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


class Video(object):
    __slots__ = strings.video_basic_fields

    def __init__(self, **kwargs):
        assert len(kwargs) == len(self.__slots__) and all(attribute in kwargs for attribute in self.__slots__)
        self.absolute_path = kwargs['absolute_path']
        self.absolute_path_hash = kwargs['absolute_path_hash']
        self.format = kwargs['format']
        self.size = kwargs['size']
        self.duration = kwargs['duration']
        self.width = kwargs['width']
        self.height = kwargs['height']
        self.video_codec = kwargs['video_codec']
        self.audio_codec = kwargs['audio_codec']
        self.frame_rate = kwargs['frame_rate']
        self.sample_rate = kwargs['sample_rate']
        self.date_added_microseconds = kwargs['date_added_microseconds']


class NewVideo(Video):
    def __init__(self, file_path):
        absolute_file_path = os.path.abspath(file_path)
        info = _get_ffprobe_json_infos(absolute_file_path)
        first_audio_stream = None
        first_video_stream = None
        assert isinstance(info['streams'], list)
        for stream in info['streams']:
            if first_audio_stream is not None and first_video_stream is not None:
                break
            codec_type = stream['codec_type']
            if codec_type == 'audio' and first_audio_stream is None:
                first_audio_stream = stream
                continue
            if codec_type == 'video' and first_video_stream is None:
                first_video_stream = stream
        assert first_video_stream is not None
        info_format = info['format']
        format = info_format['format_long_name']
        size = int(info_format['size'])
        duration = float(info_format['duration'])
        width = int(first_video_stream['width'])
        height = int(first_video_stream['height'])
        video_codec = first_video_stream['codec_name']
        audio_codec = None
        sample_rate = None
        str_frame_rate = first_video_stream['avg_frame_rate']
        if str_frame_rate in ('0', '0/0'):
            str_frame_rate = first_video_stream['r_frame_rate']
        frame_rate_pieces = str_frame_rate.split('/')
        assert len(frame_rate_pieces) in (1, 2)
        if len(frame_rate_pieces) == 1:
            frame_rate = float(frame_rate_pieces[0])
        else:
            num, den = float(frame_rate_pieces[0]), float(frame_rate_pieces[1])
            frame_rate = num / den if den != 0 else None
        if first_audio_stream is not None:
            audio_codec = first_audio_stream['codec_name']
            str_sample_rate = first_audio_stream['sample_rate']
            sample_rate_pieces = str_sample_rate.split('/')
            assert len(sample_rate_pieces) in (1, 2)
            if len(sample_rate_pieces) == 1:
                sample_rate = float(sample_rate_pieces[0])
            else:
                num, den = float(sample_rate_pieces[0]), float(sample_rate_pieces[1])
                sample_rate = num / den if den != 0 else None
        wp = whirlpool.new(absolute_file_path.encode())
        super(NewVideo, self).__init__(
            absolute_path=absolute_file_path, absolute_path_hash=wp.hexdigest(),
            format=format, size=size, duration=duration, width=width, height=height, video_codec=video_codec,
            frame_rate=frame_rate, audio_codec=audio_codec, sample_rate=sample_rate,
            date_added_microseconds=timestamp_microseconds()
        )


video_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../res/video'))
assert os.path.exists(video_path) and os.path.isdir(video_path)
for filename in os.listdir(video_path):
    basename, extension = os.path.splitext(filename)
    if extension and extension[1:] in VIDEO_SUPPORTED_EXTENSIONS:
        file_path = os.path.join(video_path, filename)
        try:
            video = NewVideo(file_path)
        except Exception:
            print('Unable to get info from file', file_path)
            raise
