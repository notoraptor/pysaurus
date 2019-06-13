import base64
import os

from moviepy.video.io.VideoFileClip import VideoFileClip

from pysaurus.core.utils.classes import Whirlpool
from pysaurus.core.error import PysaurusError


class NoClip(PysaurusError):
    pass


def video_clip(path, time_start=0, clip_seconds=10, unique_id=None):
    assert isinstance(time_start, int) and time_start >= 0
    assert isinstance(clip_seconds, int) and clip_seconds > 0
    clip = VideoFileClip(path)
    time_end = time_start + clip_seconds
    if time_start > clip.duration:
        time_start = clip.duration
    if time_end > clip.duration:
        time_end = clip.duration
    if time_start - time_end == 0:
        raise NoClip()
    if unique_id is None:
        path = os.path.abspath(path)
        unique_id = Whirlpool.hash(path)
    output_name = '%s_%s_%s.mp4' % (unique_id, time_start, clip_seconds)
    print('Taking clip from %s to %s sec in: %s' % (time_start, time_end, output_name))
    sub_clip = clip.subclip(time_start, time_end)
    sub_clip.write_videofile(output_name)
    sub_clip.close()
    clip.close()
    del clip
    del sub_clip
    return output_name


def video_clip_to_base64(path, time_start=0, clip_seconds=10, unique_id=None):
    output_path = video_clip(path, time_start, clip_seconds, unique_id)
    with open(output_path, 'rb') as file:
        content = file.read()
    encoded = base64.b64encode(content)
    print(len(encoded) / len(content))
    os.unlink(output_path)
    return encoded
