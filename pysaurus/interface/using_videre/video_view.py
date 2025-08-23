import videre
from pysaurus.properties.properties import PropUnitType
from pysaurus.video.video_pattern import VideoPattern


class VideoPropertyView(videre.Column):
    __wprops__ = {}
    __slots__ = ()

    def __init__(self, name: str, values: list[PropUnitType]):
        super().__init__(
            [videre.Text(name, strong=True)]
            + [videre.Text(str(value)) for value in values]
        )


class VideoAttributesView(videre.Column):
    __wprops__ = {}
    __slots__ = ()

    def __init__(self, video: VideoPattern, **kwargs):
        checkbox = videre.Checkbox()
        super().__init__(
            [
                videre.Row(
                    [
                        videre.ContextButton(
                            " \u2630 ", ["action 1", "act 2", "act 3"], square=True
                        ),
                        checkbox,
                        videre.Label(
                            for_button=checkbox, text=str(video.title), strong=True
                        ),
                    ],
                    vertical_alignment=videre.Alignment.CENTER,
                    space=5,
                )
            ]
            + ([videre.Text(str(video.file_title))] if video.meta_title else [])
            + [
                videre.Text(
                    str(video.filename),
                    wrap=videre.TextWrap.CHAR,
                    color=videre.Colors.blue,
                ),
                videre.Text(
                    f"{video.extension.upper()} {video.size} / "
                    f"{video.container_format} /"
                    f" ({video.video_codec}, {video.audio_codec}) / "
                    f"bite rate: {video.bit_rate}/s",
                    wrap=videre.TextWrap.WORD,
                ),
                videre.Text(
                    f"{video.length} | "
                    f"{video.width} x {video.height} @ {round(video.frame_rate)} fps, "
                    f"{video.bit_depth} bits | "
                    f"{video.sample_rate} Hz x {video.audio_bits or '32?'} bits "
                    f"({video.channels} channels), "
                    f"{video.audio_bit_rate_kbps} Kb/s",
                    wrap=videre.TextWrap.WORD,
                ),
                videre.Text(
                    f"{video.date} | "
                    f"(entry) {video.date_entry_modified} | "
                    f"(opened) {video.date_entry_opened}",
                    wrap=videre.TextWrap.WORD,
                ),
            ],
            space=2,
            **kwargs,
        )


class VideoView(videre.Container):
    __wprops__ = {}
    __slots__ = ("video",)
    __BACKGROUND_EVEN__ = videre.parse_color((240, 240, 240))

    def __init__(self, video: VideoPattern, index: int):
        self.video = video
        thumbnail = videre.Container(
            videre.Picture(video.thumbnail),
            width=300,
            horizontal_alignment=videre.Alignment.CENTER,
        )
        properties = videre.Column(
            [
                VideoPropertyView(name, values)
                for name, values in video.properties.items()
                if values
            ]
        )
        attributes = VideoAttributesView(video, weight=1)
        layout = videre.Row([thumbnail, properties, attributes], space=2)
        super().__init__(layout, padding=videre.Padding.axis(vertical=10))
        if index % 2 == 1:
            self.background_color = self.__BACKGROUND_EVEN__
