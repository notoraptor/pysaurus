import os
import sys

import av

from pysaurus.core.job_notifications import notify_job_progress
from pysaurus.core.job_utils import Job
from pysaurus.video.video import Video

# TODO Try to not import Video here
M = {jt.name: jt.short for jt in Video.__definitions__.values()}


class NoVideoStream(RuntimeError):
    pass


class NoFrameFoundInMiddleOfVideo(RuntimeError):
    pass


def open_video(filename):
    try:
        return av.open(filename)
    except UnicodeDecodeError:
        print("Opening with metadata encoding latin-1", file=sys.stderr)
        return av.open(filename, metadata_encoding="latin-1")


def _get_info(filename):
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

            d[M["filename"]] = filename
            d[M["duration"]] = container.duration
            d[M["duration_time_base"]] = av.time_base
            d[M["file_size"]] = container.size
            d[M["width"]] = video_stream.codec_context.width
            d[M["height"]] = video_stream.codec_context.height
            d[M["frame_rate_num"]] = average_rate.numerator
            d[M["frame_rate_den"]] = average_rate.denominator
            d[M["bit_depth"]] = max(
                (component.bits for component in video_stream.format.components),
                default=0,
            )
            d[M["container_format"]] = container.format.long_name
            d[M["video_codec"]] = video_stream.codec_context.codec.name
            d[M["video_codec_description"]] = video_stream.codec_context.codec.long_name
            d[M["audio_languages"]] = [
                audio_stream.language
                for audio_stream in audio_streams
                if audio_stream.language is not None
            ]
            d[M["subtitle_languages"]] = [
                subtitle_stream.language
                for subtitle_stream in subtitle_streams
                if subtitle_stream.language is not None
            ]
            if acc:
                d[M["channels"]] = acc.channels
                d[M["sample_rate"]] = acc.sample_rate
                d[M["audio_bit_rate"]] = acc.bit_rate or 0
                d[M["audio_codec"]] = acc.codec.name
                d[M["audio_codec_description"]] = acc.codec.long_name
            if meta_title is not None:
                d[M["meta_title"]] = meta_title
            if errors:
                d[M["errors"]] = list(errors)
            return d
    except Exception as exc:
        return {M["filename"]: filename, M["errors"]: [f"{type(exc).__name__}: {exc}"]}


def _get_thumbnail(filename, thumb_path, thumb_size=300):
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
                image.save(thumb_path)
                thumbnail_saved = True
                break
            if not thumbnail_saved:
                raise NoFrameFoundInMiddleOfVideo()
    except Exception as exc:
        return {
            M["filename"]: filename,
            M["errors"]: ["ERROR_SAVE_THUMBNAIL", f"{type(exc).__name__}: {exc}"],
        }
    return None


def collect_video_info(job: Job):
    _, notifier = job.args
    count = len(job.batch)
    arr = []
    for i, file_name in enumerate(job.batch):
        arr.append(_get_info(file_name))
        notify_job_progress(notifier, collect_video_info, job.id, i + 1, count)
    return arr


def collect_video_thumbnails(job: Job):
    db_folder, thumb_folder, notifier = job.args
    thumb_folder = str(thumb_folder)
    count = len(job.batch)
    arr_errors = []
    for i, (file_name, thumb_name) in enumerate(job.batch):
        thumb_path = os.path.join(thumb_folder, f"{thumb_name}.png")
        d_err = _get_thumbnail(file_name, thumb_path)
        if d_err:
            arr_errors.append(d_err)
        notify_job_progress(notifier, collect_video_thumbnails, job.id, i + 1, count)
    return arr_errors
