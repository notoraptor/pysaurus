import subprocess
import ujson as json

from pysaurus.backend.video_basic_props import VideoBasicProps
from pysaurus.utils import duration
from pysaurus.utils.absolute_path import AbsolutePath
from pysaurus.utils.exceptions import FFmpegException, FFprobeException
from pysaurus.video.video import Video


def __get_json_info(video_path):
    command = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_error', '-show_format', '-show_streams', video_path]
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    std_out, std_err = p.communicate()
    if std_err:
        raise FFprobeException(std_err)
    return json.loads(std_out)


def get_basic_props(video_path):
    info = __get_json_info(video_path)
    video_basic_props = VideoBasicProps()
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
    video_basic_props.container_format = info_format['format_long_name']
    video_basic_props.size = int(info_format['size'])
    video_basic_props.duration = float(info_format['duration'])
    video_basic_props.duration_unit = duration.SECONDS
    video_basic_props.width = int(first_video_stream['width'])
    video_basic_props.height = int(first_video_stream['height'])
    video_basic_props.video_codec = first_video_stream['codec_name']
    str_frame_rate = first_video_stream['avg_frame_rate']
    if str_frame_rate in ('0', '0/0'):
        str_frame_rate = first_video_stream['r_frame_rate']
    frame_rate_pieces = str_frame_rate.split('/')
    assert len(frame_rate_pieces) in (1, 2)
    if len(frame_rate_pieces) == 1:
        video_basic_props.frame_rate = float(frame_rate_pieces[0])
    else:
        num, den = float(frame_rate_pieces[0]), float(frame_rate_pieces[1])
        video_basic_props.frame_rate = num / den if den != 0 else None
    if first_audio_stream is not None:
        video_basic_props.audio_codec = first_audio_stream['codec_name']
        str_sample_rate = first_audio_stream['sample_rate']
        sample_rate_pieces = str_sample_rate.split('/')
        assert len(sample_rate_pieces) in (1, 2)
        if len(sample_rate_pieces) == 1:
            video_basic_props.sample_rate = float(sample_rate_pieces[0])
        else:
            num, den = float(sample_rate_pieces[0]), float(sample_rate_pieces[1])
            video_basic_props.sample_rate = num / den if den != 0 else None
    return video_basic_props


def create_thumbnail(video: Video, output_folder: AbsolutePath, output_title: str, output_extension: str = 'jpg'):
    output_file_path = AbsolutePath.new_file_path(output_folder, output_title, output_extension)
    std_out, std_err = subprocess.Popen(
        ['ffmpeg', '-y', '-ss', str(int(video.duration / 2000000)), '-i', video.absolute_path.path,
         '-vframes', '1', output_file_path.path], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if not output_file_path.exists():
        raise FFmpegException('\r\n%s\r\n%s' % (output_file_path, std_err.decode('utf-8')))
    return output_file_path
