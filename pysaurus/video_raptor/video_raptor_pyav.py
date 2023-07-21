import logging
import os

import av

from pysaurus.core.constants import JPEG_EXTENSION
from pysaurus.core.job_notifications import notify_job_progress
from pysaurus.core.parallelization import Job
from pysaurus.video_raptor.abstract_video_raptor import AbstractVideoRaptor

logger = logging.getLogger(__name__)


class NoVideoStream(RuntimeError):
    pass


class NoFrameFoundInMiddleOfVideo(RuntimeError):
    pass


def open_video(filename):
    try:
        return av.open(filename)
    except UnicodeDecodeError:
        logger.debug("Opening with metadata encoding latin-1")
        return av.open(filename, metadata_encoding="latin-1")


class VideoRaptor(AbstractVideoRaptor):
    __slots__ = ()
    RETURNS_SHORT_KEYS = False

    @classmethod
    def _get_info(cls, filename):
        try:
            with open_video(filename) as container:
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

                average_rate = video_stream.average_rate
                meta_title = container.metadata.get("title", None)

                d = {}
                errors = set()
                if not end_reachable:
                    errors.add("ERROR_SEEK_VIDEO")

                d["filename"] = filename
                d["duration"] = container.duration
                d["duration_time_base"] = av.time_base
                d["file_size"] = container.size
                d["width"] = video_stream.codec_context.width
                d["height"] = video_stream.codec_context.height
                d["frame_rate_num"] = average_rate.numerator
                d["frame_rate_den"] = average_rate.denominator
                d["bit_depth"] = max(
                    (component.bits for component in video_stream.format.components),
                    default=0,
                )
                d["container_format"] = container.format.long_name
                d["video_codec"] = video_stream.codec_context.codec.name
                d[
                    "video_codec_description"
                ] = video_stream.codec_context.codec.long_name
                d["audio_languages"] = [
                    audio_stream.language
                    for audio_stream in audio_streams
                    if audio_stream.language is not None
                ]
                d["subtitle_languages"] = [
                    subtitle_stream.language
                    for subtitle_stream in subtitle_streams
                    if subtitle_stream.language is not None
                ]
                if acc:
                    d["channels"] = acc.channels
                    d["sample_rate"] = acc.sample_rate
                    d["audio_bit_rate"] = acc.bit_rate or 0
                    d["audio_codec"] = acc.codec.name
                    d["audio_codec_description"] = acc.codec.long_name
                    d["audio_bits"] = audio_streams[0].format.bits
                if meta_title is not None:
                    d["meta_title"] = meta_title
                if errors:
                    d["errors"] = list(errors)
                return d
        except Exception as exc:
            return {"filename": filename, "errors": [f"{type(exc).__name__}: {exc}"]}

    @classmethod
    def get_thumbnail(cls, filename, thumb_path, thumb_size=300):
        try:
            with open_video(filename) as container:
                _video_streams = container.streams.video
                if not _video_streams:
                    raise NoVideoStream()
                video_stream = _video_streams[0]
                video_stream.codec_context.skip_frame = "NONKEY"
                container.seek(offset=container.duration // 2)
                thumbnail_saved = False
                for frame in container.decode(video_stream):
                    image = frame.to_image()
                    image.thumbnail((thumb_size, thumb_size))
                    image.save(thumb_path, format="JPEG")
                    thumbnail_saved = True
                    break
                if not thumbnail_saved:
                    raise NoFrameFoundInMiddleOfVideo()
        except Exception as exc:
            return {
                "filename": filename,
                "errors": ["ERROR_SAVE_THUMBNAIL", f"{type(exc).__name__}: {exc}"],
            }
        return None

    def run_thumbnail_task(
        self, notifier, task_id, filename, thumb_path, thumb_size=300
    ):
        err = self.get_thumbnail(filename, thumb_path, thumb_size)
        notify_job_progress(notifier, self.run_thumbnail_task, task_id, 1, 1)
        return err

    def collect_video_info(self, job: Job) -> list:
        _, notifier = job.args
        count = len(job.batch)
        arr = []
        for i, file_name in enumerate(job.batch):
            arr.append(self._get_info(file_name))
            notify_job_progress(notifier, self.collect_video_info, job.id, i + 1, count)
        return arr

    def collect_video_thumbnails(self, job: Job) -> list:
        db_folder, thumb_folder, notifier = job.args
        thumb_folder = str(thumb_folder)
        count = len(job.batch)
        arr_errors = []
        for i, (file_name, thumb_name) in enumerate(job.batch):
            thumb_path = os.path.join(thumb_folder, f"{thumb_name}.{JPEG_EXTENSION}")
            d_err = self.get_thumbnail(file_name, thumb_path)
            if d_err:
                arr_errors.append(d_err)
            notify_job_progress(
                notifier, self.collect_video_thumbnails, job.id, i + 1, count
            )
        return arr_errors
