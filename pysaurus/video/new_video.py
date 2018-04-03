import os

from pysaurus.backend import pyav
from pysaurus.video.video import Video


class NewVideo(Video):

    def __init__(self, file_path: str, video_id=None):
        absolute_file_path = os.path.abspath(file_path)
        video_basic_props = pyav.get_basic_props(absolute_file_path)
        super(NewVideo, self).__init__(
            absolute_path=absolute_file_path, updated=True, video_id=video_id, **video_basic_props.to_dict())
