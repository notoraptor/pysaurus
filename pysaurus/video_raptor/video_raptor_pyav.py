import logging
import sys
import traceback
from dataclasses import dataclass
from dataclasses import field as dataclass_field

import av
from PIL import Image

from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.fraction import Fraction
from pysaurus.video.video_entry import VideoEntry

logger = logging.getLogger(__name__)

ERROR_SAVE_THUMBNAIL = "ERROR_SAVE_THUMBNAIL"
ERROR_TRUNCATED_VIDEO = "ERROR_TRUNCATED_VIDEO"

# Tail check: how much is demuxed at the end of a video, and how far its last
# packet may stop short of the announced duration. Both sit two orders of
# magnitude above the noise -- a sound file ends within a frame of its
# announced duration, and an MPEG-TS duration is an estimate drifting by up to
# a second.
TAIL_WINDOW_SECONDS = 2.0
TAIL_TOLERANCE_SECONDS = 1.0


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


def _display_rotation(frame) -> int:
    """Clockwise degrees to apply to a decoded frame for display, in [0, 360).

    The display matrix rides on the frame, not on the stream: PyAV exposes it
    only as `VideoFrame.rotation`, counter-clockwise in ]-180, 180]. Pysaurus
    stores and reasons in clockwise degrees, so a portrait phone video reads
    as 90 -- the same way HandBrake and MediaInfo report it.
    """
    return -frame.rotation % 360


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
        container = None
        try:
            container = open_video(filename.path)
        except Exception as exc:
            ret.error_info = cls._exc_to_err(exc)
        else:
            if task.need_info:
                try:
                    # The thumbnail frame, when one is coming, provides the
                    # rotation, so the info pass need not decode its own frame.
                    ret.info = cls._get_info_from_container(
                        container, filename.path, read_rotation=not task.thumb_path
                    )
                except Exception as exc:
                    ret.error_info = cls._exc_to_err(exc)
            if task.thumb_path and not ret.error_info:
                try:
                    ret.thumbnail, rotation = cls._thumb_from_container(
                        container, task.thumb_path
                    )
                except Exception as exc:
                    traceback.print_tb(exc.__traceback__)
                    print(f"{type(exc).__name__}:", exc, file=sys.stderr)
                    ret.error_thumbnail = cls._exc_to_err(exc, ERROR_SAVE_THUMBNAIL)
                    rotation = cls._rotation_or_zero(container)
                if ret.info is not None:
                    ret.info.rotation = rotation
        finally:
            if container:
                container.close()
        return ret

    @classmethod
    def _get_info_from_container(
        cls, container, filename: str, read_rotation: bool = True
    ) -> VideoEntry:
        video_streams = container.streams.video
        audio_streams = container.streams.audio
        subtitle_streams = container.streams.subtitles
        if not video_streams:
            raise RuntimeError("ERROR_FIND_VIDEO_STREAM")
        if container.duration is None:
            # Used to fail as a TypeError on the end seek, which marked the
            # video unreadable; keep that outcome, say why.
            raise RuntimeError("ERROR_FIND_DURATION")
        video_stream = video_streams[0]
        acc = audio_streams[0].codec_context if audio_streams else None

        rotation = cls._rotation_from_first_frame(container) if read_rotation else 0
        complete = cls._tail_reaches_end(container, video_stream)

        # An undefined SAR reads back as None; it means square pixels.
        sar = video_stream.sample_aspect_ratio
        sar_num, sar_den = (sar.numerator, sar.denominator) if sar else (1, 1)

        average_rate = (
            video_stream.average_rate
            or video_stream.guessed_rate
            or video_stream.base_rate
            or Fraction(0)
        )

        return VideoEntry(
            filename=filename,
            duration=container.duration,
            duration_time_base=av.time_base,
            file_size=container.size,
            width=video_stream.codec_context.width,
            height=video_stream.codec_context.height,
            rotation=rotation,
            sample_aspect_ratio_num=sar_num,
            sample_aspect_ratio_den=sar_den,
            frame_rate_num=average_rate.numerator,
            frame_rate_den=average_rate.denominator,
            bit_depth=max(
                (cmp.bits for cmp in video_stream.format.components), default=0
            ),
            container_format=container.format.long_name,
            video_codec=video_stream.codec_context.codec.name,
            video_codec_description=video_stream.codec_context.codec.long_name,
            audio_languages=[
                audio_stream.language
                for audio_stream in audio_streams
                if audio_stream.language is not None
            ],
            subtitle_languages=[
                subtitle_stream.language
                for subtitle_stream in subtitle_streams
                if subtitle_stream.language is not None
            ],
            meta_title=container.metadata.get("title", ""),
            errors=([] if complete else [ERROR_TRUNCATED_VIDEO]),
            channels=acc.channels if acc else 0,
            sample_rate=acc.sample_rate if acc else 0,
            audio_bit_rate=(acc.bit_rate or 0) if acc else 0,
            audio_codec=acc.codec.name if acc else "",
            audio_codec_description=acc.codec.long_name if acc else "",
            audio_bits=audio_streams[0].format.bits if acc else 0,
        )

    @classmethod
    def _rotation_from_first_frame(cls, container) -> int:
        """Display rotation, read from the first decodable frame.

        Every frame carries the same display matrix, so which one is read does
        not matter -- only that one is. PyAV exposes no getter for it on the
        stream, hence the decoding.
        """
        video_stream = container.streams.video[0]
        container.seek(container.start_time or 0)
        for frame in container.decode(video_stream):
            return _display_rotation(frame)
        return 0

    @classmethod
    def _rotation_or_zero(cls, container) -> int:
        """Same, but for the fallback path: a failed thumbnail leaves a
        container whose decoder may well fail again, and a missing rotation
        must not turn into a missing video."""
        try:
            return cls._rotation_from_first_frame(container)
        except Exception:
            logger.debug("Could not read display rotation", exc_info=True)
            return 0

    @classmethod
    def _tail_reaches_end(cls, container, video_stream) -> bool:
        """Do the video packets run up to the duration the container announces?

        This catches a file whose data stops early, an interrupted download
        typically. Demuxing only, so it costs a couple of milliseconds; decoding
        the tail would also catch damaged data, but takes about a second per
        video and belongs to an explicit check, not to collect.

        Note an MPEG-TS carries no declared duration -- ffmpeg derives it from
        the file itself -- so a truncated one is simply a shorter valid file,
        and no test can tell.
        """
        if container.duration is None:
            return True  # nothing announced, nothing to check against
        start = container.start_time or 0
        end = start + container.duration
        window = int(TAIL_WINDOW_SECONDS * av.time_base)
        try:
            container.seek(max(start, end - window))
            # PTS are not monotonic with B-frames: keep the max, not the last.
            last_pts = max(
                (
                    packet.pts
                    for packet in container.demux(video_stream)
                    if packet.pts is not None
                ),
                default=None,
            )
        except Exception:
            logger.debug("Demuxing the tail failed", exc_info=True)
            return False
        if last_pts is None:
            return False
        gap = end / av.time_base - float(last_pts * video_stream.time_base)
        return gap <= TAIL_TOLERANCE_SECONDS

    @classmethod
    def _thumb_from_container(
        cls, container, thumb_path: str, thumb_size=300
    ) -> tuple[str, int]:
        """Save the middle-of-video thumbnail; return it with its rotation."""
        _video_streams = container.streams.video
        if not _video_streams:
            raise NoVideoStream()
        video_stream = _video_streams[0]

        start = video_stream.start_time or 0
        if video_stream.duration is not None:
            span = video_stream.duration
        elif container.duration is not None:
            # container.duration is expressed in av.time_base (microseconds).
            # Convert it to the stream time base so it can be compared to PTS.
            span = int(container.duration / av.time_base / video_stream.time_base)
        else:
            span = None

        chosen = None
        if span is None:
            # No duration at all: fall back to the very first decodable frame.
            for frame in container.decode(video_stream):
                chosen = frame
                break
        else:
            # A backward seek lands on the keyframe *preceding* the target, which
            # can be a whole GOP away. Keep decoding until the target PTS is
            # reached, so two encodings of the same content yield the same instant.
            target = start + span // 2
            container.seek(target, any_frame=False, backward=True, stream=video_stream)
            for frame in container.decode(video_stream):
                chosen = frame  # keep the last decoded frame as a fallback
                if frame.pts is not None and frame.pts >= target:
                    break

        if chosen is None:
            raise NoFrameFoundInMiddleOfVideo()
        rotation = _display_rotation(chosen)
        image: Image.Image = chosen.to_image()
        image = cls._to_display_geometry(
            image, video_stream.sample_aspect_ratio, rotation
        )
        image.thumbnail((thumb_size, thumb_size))
        image.save(thumb_path, format="JPEG")
        return thumb_path, rotation

    @classmethod
    def _to_display_geometry(cls, image: Image.Image, sar, rotation: int):
        """Turn a decoded frame into what a player would put on screen.

        `to_image()` gives the stored pixels: neither the sample aspect ratio
        nor the display matrix is applied. A no-op for square pixels with no
        rotation, which is the common case.
        """
        if sar and sar.numerator != sar.denominator:
            width, height = image.size
            display_width = max(1, round(width * sar.numerator / sar.denominator))
            image = image.resize((display_width, height), Image.Resampling.LANCZOS)
        if rotation:
            # PIL rotates counter-clockwise, and takes an exact transpose path
            # for the multiples of 90 a display matrix uses.
            image = image.rotate(-rotation, expand=True)
        return image

    @classmethod
    def _exc_to_err(cls, exc: Exception, *extra_errors) -> list[str]:
        return [*extra_errors, f"{type(exc).__name__}: {exc}"]
