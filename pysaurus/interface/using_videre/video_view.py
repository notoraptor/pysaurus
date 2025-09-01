from typing import Callable

import videre

from pysaurus.core import notifications
from pysaurus.interface.using_videre.backend import get_backend
from pysaurus.properties.properties import PropUnitType
from pysaurus.video.video_pattern import VideoPattern

LIGHT_GREY = videre.parse_color((240, 240, 240))


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
    __slots__ = ("_video", "_menu", "_text_path")

    def __init__(self, video: VideoPattern, **kwargs):
        checkbox = videre.Checkbox()
        properties = video.properties
        self._video = video
        self._menu = videre.ContextButton(
            " \u2630 ",
            actions=self._get_menu_actions(video),
            square=True,
        )
        self._text_path = videre.Text(
            str(video.filename),
            wrap=videre.TextWrap.CHAR,
            color=videre.Colors.lightgray if video.watched else videre.Colors.blue,
            strong=video.watched,
        )
        super().__init__(
            [
                videre.Row(
                    [
                        self._menu,
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
                self._text_path,
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
                videre.Text(
                    f"Audio: {', '.join(video.audio_languages or ['(none)'])} | "
                    f"Subtitles: {', '.join(video.subtitle_languages or ['(none)'])}"
                ),
                videre.Text(f"Similarity: {video.similarity}"),
            ]
            + (
                [
                    videre.Text("PROPERTIES", strong=True),
                    *(
                        videre.Row(
                            [
                                videre.Text(f"{name}:", strong=True),
                                *(
                                    videre.Container(
                                        videre.Text(str(value), italic=True),
                                        background_color=LIGHT_GREY,
                                        padding=videre.Padding.axis(2, 4),
                                    )
                                    for value in values
                                ),
                            ],
                            space=5,
                            vertical_alignment=videre.Alignment.CENTER,
                        )
                        for name, values in properties.items()
                    ),
                ]
                if properties
                else []
            ),
            space=2,
            **kwargs,
        )

    def _action_open_file(self):
        get_backend(self).open_video(self._video.video_id)
        self.get_window().notify(notifications.Message("Opened:", self._video.filename))

    def _action_open_containing_folder(self):
        ret = get_backend(self).open_containing_folder(self._video.video_id)
        self.get_window().notify(notifications.Message("Opened folder:", ret))

    def _action_change_watched(self):
        backend = get_backend(self)
        watched = backend.mark_as_read(self._video.video_id)
        video = backend.get_video(self._video.video_id)
        assert video.watched is watched
        self._video = video
        self._text_path.color = (
            videre.Colors.lightgray if video.watched else videre.Colors.blue
        )
        self._text_path.strong = watched
        self._menu.actions = self._get_menu_actions(video)

    def _get_menu_actions(self, video: VideoPattern) -> list[tuple[str, Callable]]:
        return [
            (
                f"Mark as {'unwatched' if video.watched else 'watched'}",
                self._action_change_watched,
            ),
            ("Open file", self._action_open_file),
            ("Open containing folder", self._action_open_containing_folder),
        ]


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
        attributes = VideoAttributesView(video, weight=1)
        layout = videre.Row([thumbnail, attributes], space=6)
        super().__init__(layout, padding=videre.Padding.axis(vertical=10))
        if index % 2 == 1:
            self.background_color = self.__BACKGROUND_EVEN__
