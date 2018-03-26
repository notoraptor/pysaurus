import os

import pymediainfo

from pysaurus.video import Video


class NewVideo(Video):

    def __init__(self, file_path: str, video_id=None):
        absolute_file_path = os.path.abspath(file_path)
        media_info = pymediainfo.MediaInfo.parse(absolute_file_path)
        general_stream = None
        first_audio_stream = None
        first_video_stream = None
        for track in media_info.tracks:
            if all(stream is not None for stream in (general_stream, first_video_stream, first_audio_stream)):
                break
            if track.track_type == 'General':
                if general_stream is None:
                    general_stream = track
            elif track.track_type == 'Video':
                if first_video_stream is None:
                    first_video_stream = track
            elif track.track_type == 'Audio':
                if first_audio_stream is None:
                    first_audio_stream = track
        assert general_stream is not None
        assert first_video_stream is not None
        movie_name = general_stream.movie_name
        movie_title = general_stream.title
        container_format = general_stream.format
        size = int(general_stream.file_size)
        duration = int(general_stream.duration)  # milliseconds
        width = int(first_video_stream.width)
        height = int(first_video_stream.height)
        video_codec = first_video_stream.format
        frame_rate = float(first_video_stream.frame_rate)
        audio_codec, sample_rate = None, None
        if first_audio_stream is not None:
            sample_rate = first_audio_stream.sampling_rate
            if isinstance(sample_rate, str) and '/' in sample_rate:
                sample_rate = max(float(piece.strip()) for piece in sample_rate.split('/'))
            audio_codec = first_audio_stream.format

        super(NewVideo, self).__init__(
            absolute_path=absolute_file_path, container_format=container_format,
            movie_name=movie_name, movie_title=movie_title,
            size=size, duration=duration, width=width, height=height, video_codec=video_codec,
            frame_rate=frame_rate, audio_codec=audio_codec, sample_rate=sample_rate,
            updated=True, video_id=video_id
        )
