import os

from pysaurus.new_video import NewVideo
from pysaurus.utils import VIDEO_SUPPORTED_EXTENSIONS

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
