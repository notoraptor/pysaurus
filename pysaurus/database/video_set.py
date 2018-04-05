from pysaurus.utils.absolute_path import AbsolutePath
from pysaurus.video.video import Video


class VideoSet(object):
    __slots__ = '__videos',

    def __init__(self):
        self.__videos = {}  # type: dict{AbsolutePath, Video}

    def add(self, video: Video, update=False):
        if not update:
            assert video.absolute_path not in self.__videos
        self.__videos[video.absolute_path] = video

    def remove_from_absolute_path(self, absolute_path: AbsolutePath):
        return self.__videos.pop(absolute_path)

    def contains(self, video: Video):
        return video.absolute_path in self.__videos

    def contains_absolute_path(self, absolute_path: AbsolutePath):
        return absolute_path in self.__videos

    def get_from_absolute_path(self, absolute_path: AbsolutePath):
        """ Return Video associated to given absolute path.
            Raise an error if this path is not associated to any video object in database,
        :param absolute_path: absolute path for video to get Video object.
        :return: a Video object.
        :rtype: Video
        """
        return self.__videos[absolute_path]

    def videos(self):
        return self.__videos.values()

    def video_paths(self):
        return self.__videos.keys()
