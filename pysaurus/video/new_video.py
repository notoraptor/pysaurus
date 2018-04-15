import os

from pysaurus.backend import pyav
from pysaurus.video.video import Video


class NewVideo(Video):

    def __init__(self, file_path: str, video_id=None):
        super(NewVideo, self).__init__()
        absolute_file_path = os.path.abspath(file_path)
        pyav.get_basic_props(absolute_file_path, self)
        self.updated = True
        self.video_id = video_id
        self.validate()
