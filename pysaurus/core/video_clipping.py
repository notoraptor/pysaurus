import base64
import os

from moviepy.video.io.VideoFileClip import VideoFileClip

from pysaurus.core.utils.classes import Whirlpool
from pysaurus.core.error import PysaurusError

class NoMoreClips(PysaurusError):
    pass


def video_clip(path, clip_index=0, clip_seconds=10, unique_id=None):
    assert isinstance(clip_index, int) and clip_index >= 0
    assert isinstance(clip_seconds, int) and clip_seconds > 0
    clip = VideoFileClip(path)
    nb_clips = (clip.duration // clip_seconds) + bool(clip.duration % clip_seconds)
    if clip_index >= nb_clips:
        raise NoMoreClips()
    time_start = clip_seconds * clip_index
    time_end = clip_seconds * (clip_index + 1)
    if time_end > clip.duration:
        time_end = clip.duration
    if unique_id is None:
        path = os.path.abspath(path)
        unique_id = Whirlpool.hash(path)
    output_name = '%s_%s_%s.mp4' % (unique_id, clip_index, clip_seconds)
    print('Taking clip %d of %d, from %s to %s sec in: %s' % (
        clip_index + 1, nb_clips, time_start, time_end, output_name))
    clip.subclip(time_start, time_end).write_videofile(output_name)
    return output_name


def video_clip_to_base64(path, clip_index=0, clip_seconds=10, unique_id=None):
    output_path = video_clip(path, clip_index, clip_seconds, unique_id)
    with open(output_path, 'rb') as file:
        content = file.read()
    encoded = base64.b64encode(content)
    print(len(encoded) / len(content))
    os.unlink(output_path)
    return encoded
