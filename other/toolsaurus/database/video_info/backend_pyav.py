from pysaurus.core.jsonable import Jsonable
from pysaurus.video_info.backend_pyav import open_video


class StreamInfo(Jsonable):
    lang_code = ""
    short_name = ""
    long_name = ""


class StreamsInfo:
    def __init__(self, *, audio=(), subtitle=()):
        self.audio = audio
        self.subtitle = subtitle

    @classmethod
    def get(cls, filename):
        with open_video(filename) as container:
            return cls(
                audio=[
                    StreamInfo(
                        lang_code=audio_stream.language,
                        short_name=audio_stream.codec_context.codec.name,
                        long_name=audio_stream.codec_context.codec.long_name,
                    )
                    for audio_stream in container.streams.audio
                ],
                subtitle=[
                    StreamInfo(
                        lang_code=subtitle_stream.language,
                        short_name=subtitle_stream.codec_context.codec.name,
                        long_name=subtitle_stream.codec_context.codec.long_name,
                    )
                    for subtitle_stream in container.streams.subtitles
                ],
            )

    def __str__(self):
        return f"audio {self.audio} subtitle {self.subtitle}"

    __repr__ = __str__
