import logging
import sys
import traceback
from dataclasses import dataclass
from dataclasses import field as dataclass_field

import av
from PIL import Image

from pysaurus.core.components import AbsolutePath
from pysaurus.core.fraction import Fraction
from pysaurus.video.video_entry import VideoEntry

logger = logging.getLogger(__name__)

ERROR_SAVE_THUMBNAIL = "ERROR_SAVE_THUMBNAIL"


class NoVideoStream(RuntimeError):
    pass


class NoFrameFoundInMiddleOfVideo(RuntimeError):
    pass


class VideoTask:
    __slots__ = ("filename", "need_info", "thumb_path")

    def __init__(
        self,
        filename: AbsolutePath,
        need_info: bool = False,
        thumb_path: str | None = None,
    ):
        assert need_info or thumb_path
        self.filename = filename
        self.need_info = need_info
        self.thumb_path = thumb_path


@dataclass(slots=True)
class VideoTaskResult:
    task: VideoTask
    info: VideoEntry | None = None
    thumbnail: str | None = None
    error_info: list[str] = dataclass_field(default_factory=list)
    error_thumbnail: list[str] = dataclass_field(default_factory=list)

    def get_unreadable(self) -> VideoEntry:
        return VideoEntry(
            filename=self.task.filename.path,
            errors=sorted(self.error_info),
            unreadable=True,
        )


def open_video(filename: str):
    try:
        return av.open(filename)
    except UnicodeDecodeError:
        logger.debug("Opening with metadata encoding latin-1")
        return av.open(filename, metadata_encoding="latin-1")


class PythonVideoRaptor:
    __slots__ = ()

    @classmethod
    def capture(cls, task: VideoTask) -> VideoTaskResult:
        filename = task.filename
        ret = VideoTaskResult(task=task)
        try:
            container = open_video(filename.path)
        except Exception as exc:
            ret.error_info = cls._exc_to_err(exc)
        else:
            if task.need_info:
                try:
                    ret.info = cls._get_info_from_container(container, filename.path)
                except Exception as exc:
                    ret.error_info = cls._exc_to_err(exc)
            if task.thumb_path and not ret.error_info:
                try:
                    ret.thumbnail = cls._thumb_from_container(
                        container, task.thumb_path
                    )
                except Exception as exc:
                    traceback.print_tb(exc.__traceback__)
                    print(f"{type(exc).__name__}:", exc, file=sys.stderr)
                    ret.error_thumbnail = cls._exc_to_err(exc, ERROR_SAVE_THUMBNAIL)
            container.close()
        return ret

    @classmethod
    def _get_info_from_container(cls, container, filename: str) -> VideoEntry:
        video_streams = container.streams.video
        audio_streams = container.streams.audio
        subtitle_streams = container.streams.subtitles
        if not video_streams:
            raise RuntimeError("ERROR_FIND_VIDEO_STREAM")
        video_stream = video_streams[0]
        acc = audio_streams[0].codec_context if audio_streams else None
        video_stream.codec_context.skip_frame = "NONKEY"

        end_reachable = False
        container.seek(offset=container.duration - 1)
        for _ in container.decode(video_stream):
            end_reachable = True
            break

        average_rate = (
            video_stream.average_rate
            or video_stream.guessed_rate
            or video_stream.base_rate
            or Fraction(0)
        )

        return VideoEntry(
            **{
                "filename": filename,
                "duration": container.duration,
                "duration_time_base": av.time_base,
                "file_size": container.size,
                "width": video_stream.codec_context.width,
                "height": video_stream.codec_context.height,
                "frame_rate_num": average_rate.numerator,
                "frame_rate_den": average_rate.denominator,
                "bit_depth": max(
                    (cmp.bits for cmp in video_stream.format.components), default=0
                ),
                "container_format": container.format.long_name,
                "video_codec": video_stream.codec_context.codec.name,
                "video_codec_description": video_stream.codec_context.codec.long_name,
                "audio_languages": [
                    audio_stream.language
                    for audio_stream in audio_streams
                    if audio_stream.language is not None
                ],
                "subtitle_languages": [
                    subtitle_stream.language
                    for subtitle_stream in subtitle_streams
                    if subtitle_stream.language is not None
                ],
                "meta_title": container.metadata.get("title", ""),
                "errors": ([] if end_reachable else ["ERROR_SEEK_END_VIDEO"]),
                **(
                    {
                        "channels": acc.channels,
                        "sample_rate": acc.sample_rate,
                        "audio_bit_rate": acc.bit_rate or 0,
                        "audio_codec": acc.codec.name,
                        "audio_codec_description": acc.codec.long_name,
                        "audio_bits": audio_streams[0].format.bits,
                    }
                    if acc
                    else {}
                ),
            }
        )

    @classmethod
    def _thumb_from_container(cls, container, thumb_path: str, thumb_size=300) -> str:
        _video_streams = container.streams.video
        if not _video_streams:
            raise NoVideoStream()
        video_stream = _video_streams[0]
        # video_stream.codec_context.skip_frame = "NONKEY"
        if video_stream.duration is not None:
            container.seek(
                offset=video_stream.duration // 2,
                any_frame=False,
                backward=True,
                stream=video_stream,
            )
        else:
            container.seek(
                offset=container.duration // 2, any_frame=False, backward=True
            )
        for frame in container.decode(video_stream):
            image: Image.Image = frame.to_image()
            image.thumbnail((thumb_size, thumb_size))
            image.save(thumb_path, format="JPEG")
            break
        else:
            raise NoFrameFoundInMiddleOfVideo()
        return thumb_path

    @classmethod
    def _exc_to_err(cls, exc: Exception, *extra_errors) -> list[str]:
        return [*extra_errors, f"{type(exc).__name__}: {exc}"]
