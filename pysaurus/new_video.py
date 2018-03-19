import os

from pysaurus.utils import ffmpeg_backend
from pysaurus.video import Video


class NewVideo(Video):

    def __init__(self, file_path):
        absolute_file_path = os.path.abspath(file_path)
        info = ffmpeg_backend.get_json_info(absolute_file_path)
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
        container_format = info_format['format_long_name']
        size = int(info_format['size'])
        duration = float(info_format['duration'])
        width = int(first_video_stream['width'])
        height = int(first_video_stream['height'])
        video_codec = first_video_stream['codec_name']
        audio_codec, sample_rate = None, None
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

        super(NewVideo, self).__init__(
            absolute_path=absolute_file_path, container_format=container_format,
            size=size, duration=duration, width=width, height=height, video_codec=video_codec,
            frame_rate=frame_rate, audio_codec=audio_codec, sample_rate=sample_rate,
            updated=True,
        )
