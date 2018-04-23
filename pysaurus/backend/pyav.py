import av

from pysaurus.utils import duration
from pysaurus.utils.absolute_path import AbsolutePath
from pysaurus.utils.common import get_convenient_os_path
from pysaurus.utils.exceptions import PyavThumbnailException
from pysaurus.video.video import Video


def get_basic_props(video_path, video):
    """
    :param video_path:
    :param video:
    :type video: Video
    """
    container = av.open(get_convenient_os_path(video_path))
    assert container.streams.video
    video_stream = container.streams.video[0]

    video.absolute_path = video_path
    video.duration = container.duration
    video.duration_unit = duration.MICROSECONDS
    video.size = container.size  # number of bytes
    video.container_format = container.format.long_name
    video.width = video_stream.width
    video.height = video_stream.height
    video.video_codec = video_stream.long_name
    video.frame_rate = float(video_stream.average_rate or 1 / video_stream.time_base)
    if container.streams.audio:
        audio_stream = container.streams.audio[0]
        video.audio_codec = audio_stream.long_name
        video.sample_rate = audio_stream.rate


def create_thumbnail(video: Video, output_folder: AbsolutePath, output_title, output_extension='jpg'):
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
