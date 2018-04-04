import sys

import av

from pysaurus.backend.video_basic_props import VideoBasicProps
from pysaurus.utils import duration
from pysaurus.utils.absolute_path import AbsolutePath
from pysaurus.utils.exceptions import PyavThumbnailException
from pysaurus.video.video import Video


def get_short_path_name(long_name):
    """
    Gets the short path name of a given long path.
    http://stackoverflow.com/a/23598461/200291
    """
    if not sys.platform.startswith('win'):
        return long_name
    import ctypes
    from ctypes import wintypes
    _GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
    _GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    _GetShortPathNameW.restype = wintypes.DWORD
    output_buf_size = 0
    while True:
        output_buf = ctypes.create_unicode_buffer(output_buf_size)
        needed = _GetShortPathNameW(long_name, output_buf, output_buf_size)
        if output_buf_size >= needed:
            return output_buf.value
        else:
            output_buf_size = needed


def get_basic_props(video_path):
    # container = av.open(get_short_path_name(video_path))
    container = av.open(video_path)
    assert container.streams.video
    video_stream = container.streams.video[0]

    video_basic_props = VideoBasicProps()
    video_basic_props.duration = int(container.duration)
    video_basic_props.duration_unit = duration.MICROSECONDS
    video_basic_props.size = int(container.size)  # number of bytes
    video_basic_props.container_format = container.format.long_name
    video_basic_props.width = int(video_stream.width)
    video_basic_props.height = int(video_stream.height)
    video_basic_props.video_codec = video_stream.long_name
    video_basic_props.frame_rate = float(video_stream.average_rate)
    if container.streams.audio:
        audio_stream = container.streams.audio[0]
        video_basic_props.audio_codec = audio_stream.long_name
        video_basic_props.sample_rate = audio_stream.rate

    return video_basic_props


def create_thumbnail(video: Video, output_folder: AbsolutePath, output_title: str, output_extension: str = 'jpg'):
    output_file_path = AbsolutePath.new_file_path(output_folder, output_title, output_extension)
    container = av.open(str(video.absolute_path))
    assert container.streams.video
    try:
        container.seek(int(container.duration / 2000000), 'time', True, True)
    except OverflowError as e:
        print('ERROR WITH', container.duration, 2000000, container.duration / 2000000)
        raise e
    for frame in container.decode(video=0):
        frame.to_image().save(str(output_file_path))
        break
    if not output_file_path.exists():
        raise PyavThumbnailException(output_file_path)
    return output_file_path
