from typing import List

import flet as ft

from pysaurus.interface.flet_interface.page.videos_page_utils import VideoStateWrapper
from pysaurus.properties.properties import PropTypeDesc

PREFIX = "data:image/jpeg;base64,"


class VideoView(ft.Row):
    def __init__(
        self, video: VideoStateWrapper, prop_types: List[PropTypeDesc], index=None
    ):
        super().__init__(vertical_alignment=ft.CrossAxisAlignment.START)
        thumbnail = video.thumbnail_path
        if thumbnail:
            image = ft.Image(src_base64=thumbnail[len(PREFIX) :])
        else:
            image = ft.Text(
                "NO THUMBNAIL", weight=ft.FontWeight.BOLD, color=ft.colors.GREY
            )

        prop_panel = []
        for prop_type in prop_types:
            if prop_type.name in video.properties:
                values = video.properties[prop_type.name]
                prop_panel.append(
                    ft.Column(
                        [
                            ft.Row(
                                [ft.Text(prop_type.name, weight=ft.FontWeight.BOLD)],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            ft.Container(
                                ft.Text(
                                    spans=[
                                        ft.TextSpan(
                                            val,
                                            ft.TextStyle(bgcolor=ft.colors.GREY),
                                        )
                                        for val in values
                                    ],
                                    text_align=ft.TextAlign.CENTER
                                ),
                                bgcolor=ft.colors.GREEN,
                                alignment=ft.alignment.center
                            ),
                        ]
                    )
                )

        self.controls = [
            ft.Container(image, width=300, alignment=ft.alignment.center),
            ft.Container(
                ft.Column(
                    [
                        ft.ElevatedButton(text="Properties", icon=ft.icons.SETTINGS),
                        ft.Container(ft.Column(prop_panel), bgcolor=ft.colors.YELLOW),
                    ]
                ),
                bgcolor=ft.colors.PINK,
                expand=3,
            ),
            ft.Text(video.filename, expand=7),
        ]
