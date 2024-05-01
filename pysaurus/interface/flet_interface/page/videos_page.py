import flet as ft

from pysaurus.interface.flet_interface.flet_utils import FletUtils, Title2

PAGE_SIZES = [1, 10, 20, 50, 100]

VIDEO_DEFAULT_PAGE_SIZE = PAGE_SIZES[-1]

VIDEO_DEFAULT_PAGE_NUMBER = 0


class VideosPage(ft.Column):
    def __init__(self):
        super().__init__(
            [
                ft.Row([ft.ProgressRing()], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row(
                    [Title2("Loading videos ...")],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def did_mount(self):
        self.page.run_task(self.load_videos)

    async def load_videos(self):
        interface = FletUtils.get_app_interface(self)
        state = interface.backend(VIDEO_DEFAULT_PAGE_SIZE, VIDEO_DEFAULT_PAGE_NUMBER)
        self.controls = [ft.Text(f"{len(state['videos'])} video(s)")]
        self.update()
