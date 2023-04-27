from pysaurus.core.json_type import Type
from pysaurus.core.schematizable import Schema, WithSchema, schema_prop
from pysaurus.video_raptor.video_raptor_pyav import open_video


class StreamInfo(WithSchema):
    __slots__ = ()
    SCHEMA = Schema(
        (
            Type("lang_code", None, ""),
            Type("short_name", None, ""),
            Type("long_name", None, ""),
        )
    )
    lang_code = schema_prop("lang_code")
    short_name = schema_prop("short_name")
    long_name = schema_prop("long_name")


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
