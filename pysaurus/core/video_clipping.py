import base64
import os

import av

from pysaurus.core import core_exceptions
from pysaurus.core.modules import FNV64, FileSystem


class VideoClipping:
    @staticmethod
    def video_clip(path, time_start=0, clip_seconds=10, unique_id=None):
        assert isinstance(time_start, int) and time_start >= 0
        assert isinstance(clip_seconds, int) and clip_seconds > 0

        input_container = av.open(path)
        in_stream = input_container.streams.video[0]
        duration = float(in_stream.duration * in_stream.time_base)

        time_end = time_start + clip_seconds
        if time_start > duration:
            time_start = duration
        if time_end > duration:
            time_end = duration
        if time_start - time_end == 0:
            input_container.close()
            raise core_exceptions.ZeroLengthError()

        if unique_id is None:
            path = os.path.abspath(path)
            unique_id = FNV64.hash(path)
        output_name = f"{unique_id}_{time_start}_{clip_seconds}.mp4"
        print("Clip from", time_start, "to", time_end, "sec in:", output_name)

        output_container = av.open(output_name, mode="w")
        out_stream = output_container.add_stream("h264", rate=in_stream.average_rate)
        out_stream.width = in_stream.codec_context.width
        out_stream.height = in_stream.codec_context.height
        out_stream.pix_fmt = "yuv420p"

        input_container.seek(int(time_start / av.time_base), backward=True)
        for frame in input_container.decode(in_stream):
            if frame.time < time_start:
                continue
            if frame.time >= time_end:
                break
            for packet in out_stream.encode(frame):
                output_container.mux(packet)

        for packet in out_stream.encode():
            output_container.mux(packet)

        output_container.close()
        input_container.close()
        return output_name

    @staticmethod
    def video_clip_to_base64(path, time_start=0, clip_seconds=10, unique_id=None):
        output_path = VideoClipping.video_clip(
            path, time_start, clip_seconds, unique_id
        )
        with open(output_path, "rb") as file:
            content = file.read()
        encoded = base64.b64encode(content)
        print(len(encoded) / len(content))
        FileSystem.unlink(output_path)
        return encoded
