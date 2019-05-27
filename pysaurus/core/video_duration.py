from pysaurus.core.duration import Duration


class VideoDuration(Duration):

    def __init__(self, video):
        """ Video duration is number of seconds * video time base.
            So, number of seconds = video duration / video time base.
            :param video: video to get duration.
            :type video: pysaurus.core.video.Video
        """
        super(VideoDuration, self).__init__(round(video.duration * 1000000 / video.duration_time_base))
