from typing import Callable

import flet as ft

from pysaurus.core.functions import expand_if
from pysaurus.interface.flet_interface.flet_custom_widgets import CUSTOM_FONT_MONOSPACE
from pysaurus.properties.properties import PropTypeDesc
from pysaurus.video.javascript_video import JavascriptVideo

_BACKGROUND_COLORS_ = [
    # not found, then even index, odd index
    ["#fafac8", "#fafa8c"],
    # found, then even index, odd index
    [ft.colors.WHITE, "#f0f0f0"],
]


class VideoView(ft.Container):
    def __init__(
        self,
        video: JavascriptVideo,
        prop_types: list[PropTypeDesc],
        index=None,
        common_fields: dict[str, bool] = None,
        grouped_by_similarity=False,
        grouped_by_moves=False,
        is_selected=False,
        on_select: Callable[[int, bool], None] = None,
    ):
        super().__init__(padding=5)
        self.video = video
        self.callback_on_select = on_select

        thumbnail = video.thumbnail_base64
        if thumbnail:
            image = ft.Image(src_base64=thumbnail)
        else:
            image = ft.Text(
                "NO THUMBNAIL", weight=ft.FontWeight.BOLD, color=ft.colors.GREY
            )

        props_view = []
        for prop_type in prop_types:
            if prop_type.name in video.properties:
                values = video.properties[prop_type.name]
                props_view.extend(
                    [
                        ft.Container(
                            ft.Row(
                                [ft.Text(prop_type.name, weight=ft.FontWeight.BOLD)],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            bgcolor=ft.colors.GREEN_50,
                        ),
                        ft.Container(
                            ft.Row(
                                [
                                    ft.Text(val, bgcolor=ft.colors.GREY)
                                    for val in values
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                wrap=True,
                            ),
                            bgcolor=ft.colors.GREEN,
                            alignment=ft.alignment.center,
                        ),
                    ]
                )

        audio_bit_rate = round(video.audio_bit_rate / 1000)
        extension = video.extension.upper()
        frame_rate = round(video.frame_rate)
        meta_title = None if video.title == video.file_title else video.title
        unique_move = (
            video.moves[0] if grouped_by_moves and len(video.moves) == 1 else None
        )
        errors = sorted(video.errors)

        self.checkbox = ft.Checkbox(
            video.title,
            label_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
            value=bool(is_selected),
            on_change=self.on_select,
        )

        self.bgcolor = _BACKGROUND_COLORS_[video.found][index % 2]
        self.content = ft.Row(
            [
                ft.Container(image, width=300, alignment=ft.alignment.center),
                ft.Container(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.ElevatedButton(
                                        text="Properties",
                                        icon=ft.icons.SETTINGS,
                                        style=ft.ButtonStyle(
                                            shape=ft.RoundedRectangleBorder()
                                        ),
                                        expand=True,
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            ft.Container(
                                ft.Column(props_view), bgcolor=ft.colors.YELLOW
                            ),
                        ]
                    ),
                    bgcolor=ft.colors.PINK,
                    expand=25,
                ),
                ft.Container(
                    ft.Column(
                        [
                            self.checkbox,
                            *expand_if(meta_title and ft.Text(meta_title, italic=True)),
                            ft.Text(video.filename, font_family="Roboto Mono"),
                            ft.Row(
                                [
                                    ft.Text(extension),
                                    ft.Text(video.size, tooltip=str(video.file_size)),
                                    ft.Text(video.container_format),
                                    ft.Text(
                                        video.video_codec,
                                        tooltip=video.video_codec_description,
                                    ),
                                    ft.Text(
                                        video.audio_codec,
                                        tooltip=video.audio_codec_description,
                                    ),
                                    ft.Text(
                                        f"{video.bit_rate}/s", weight=ft.FontWeight.BOLD
                                    ),
                                ],
                                wrap=True,
                            ),
                            ft.Row(
                                [
                                    ft.Text(video.length),
                                    ft.Text(
                                        f"{video.width} x {video.height} @ {frame_rate} fps"
                                    ),
                                    ft.Text(f"{video.bit_depth} bits"),
                                    ft.Text(
                                        f"{video.sample_rate} Hz x "
                                        f"{video.audio_bits or '32?'} bits "
                                        f"({video.channels} channels)"
                                    ),
                                    ft.Text(f"{audio_bit_rate} Kb/s"),
                                ],
                                wrap=True,
                            ),
                            ft.Row(
                                [
                                    ft.Text(
                                        video.date, font_family=CUSTOM_FONT_MONOSPACE
                                    ),
                                    ft.Text("(entry)"),
                                    ft.Text(
                                        video.date_entry_modified,
                                        font_family=CUSTOM_FONT_MONOSPACE,
                                    ),
                                    ft.Text("(opened)"),
                                    ft.Text(
                                        video.date_entry_opened,
                                        font_family=CUSTOM_FONT_MONOSPACE,
                                    ),
                                ],
                                wrap=True,
                            ),
                            ft.Row(
                                [
                                    ft.Text("Audio:"),
                                    ft.Text(
                                        (
                                            ", ".join(video.audio_languages)
                                            if video.audio_languages
                                            else "(none)"
                                        ),
                                        font_family=CUSTOM_FONT_MONOSPACE,
                                    ),
                                ],
                                wrap=True,
                            ),
                            ft.Row(
                                [
                                    ft.Text("Subtitles:"),
                                    ft.Text(
                                        (
                                            ", ".join(video.subtitle_languages)
                                            if video.subtitle_languages
                                            else "(none)"
                                        ),
                                        font_family=CUSTOM_FONT_MONOSPACE,
                                    ),
                                ],
                                wrap=True,
                            ),
                            *expand_if(
                                errors
                                and ft.Row(
                                    [
                                        ft.Text("Errors:"),
                                        *[
                                            ft.Text(
                                                error, font_family=CUSTOM_FONT_MONOSPACE
                                            )
                                            for error in errors
                                        ],
                                    ],
                                    wrap=True,
                                )
                            ),
                            *expand_if(
                                grouped_by_similarity
                                and ft.Row(
                                    [
                                        ft.Text("Similarity ID:"),
                                        ft.Text(
                                            "(not yet compared)"
                                            if video.similarity_id is None
                                            else (
                                                "(no similarities)"
                                                if video.similarity_id == -1
                                                else video.similarity_id
                                            )
                                        ),
                                    ],
                                    wrap=True,
                                )
                            ),
                            *expand_if(
                                unique_move
                                and ft.ElevatedButton(
                                    content=ft.Row(
                                        [
                                            ft.Text("confirm move to:"),
                                            ft.Text(
                                                unique_move["filename"],
                                                font_family=CUSTOM_FONT_MONOSPACE,
                                            ),
                                        ]
                                    ),
                                    icon=ft.icons.MOVING,
                                )
                            ),
                        ]
                    ),
                    expand=75,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    def on_select(self, e: ft.ControlEvent):
        if self.callback_on_select:
            self.callback_on_select(self.video.video_id, e.control.value)

    def set_select(self, is_selected: bool):
        self.checkbox.value = bool(is_selected)
