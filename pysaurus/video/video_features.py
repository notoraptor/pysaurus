from typing import Iterable

from pysaurus.core.functions import class_get_public_attributes
from pysaurus.video import Video

VIDEO_FIELDS = class_get_public_attributes(Video)


class VideoFeatures:
    @staticmethod
    def json(video: Video, with_moves=False) -> dict:
        return {
            "audio_bit_rate": video.audio_bit_rate,
            "audio_bits": video.audio_bits,
            "audio_codec": video.audio_codec.value,
            "audio_codec_description": video.audio_codec_description.value,
            "audio_languages": video.audio_languages,
            "bit_depth": video.bit_depth,
            "bit_rate": str(video.bit_rate),
            "channels": video.channels,
            "container_format": video.container_format.value,
            "date": str(video.date),
            "date_entry_modified": str(video.date_entry_modified),
            "date_entry_opened": str(video.date_entry_opened),
            "day": video.day,
            "device_name": video.device_name.value,
            "disk": video.disk,
            "duration": video.duration,
            "duration_time_base": video.duration_time_base,
            "errors": list(video.errors),
            "extension": video.extension,
            "file_size": video.file_size,
            "file_title": video.file_title.value,
            "file_title_numeric": str(video.file_title_numeric),
            "filename": str(video.filename),
            "filename_numeric": str(video.filename_numeric),
            "found": video.found,
            "frame_rate": video.frame_rate,
            "frame_rate_den": video.frame_rate_den,
            "frame_rate_num": video.frame_rate_num,
            "height": video.height,
            "length": str(video.length),
            "meta_title": video.meta_title.value,
            "meta_title_numeric": str(video.meta_title_numeric),
            "move_id": video.move_id if with_moves else None,
            "moves": video.moves if with_moves else None,
            "not_found": video.not_found,
            "properties": video.json_properties,
            "readable": video.readable,
            "sample_rate": video.sample_rate,
            "similarity_id": video.similarity_id,
            "size": str(video.size),
            "size_length": str(video.size_length),
            "subtitle_languages": video.subtitle_languages,
            "thumbnail_path": video.thumbnail_base64,
            "title": video.title.value,
            "title_numeric": str(video.title_numeric),
            "video_codec": video.video_codec.value,
            "video_codec_description": video.video_codec_description.value,
            "video_id": video.video_id,
            "width": video.width,
            "with_thumbnails": video.with_thumbnails,
        }

    @staticmethod
    def get_common_fields(videos: Iterable, getfield=getattr):
        videos = list(videos)
        if len(videos) < 2:
            return {}
        first_video, *other_videos = videos
        return {
            key: all(
                getfield(first_video, key) == getfield(other_video, key)
                for other_video in other_videos
            )
            for key in VIDEO_FIELDS
        }
