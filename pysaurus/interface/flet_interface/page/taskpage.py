"""
NB: Code is currently wrong, notably around progress bars.
"""

from typing import Sequence

import flet as ft

from pysaurus.core.notifications import Notification
from pysaurus.core.overridden import Overridden
from pysaurus.interface.flet_interface.flet_custom_widgets import Title1
from pysaurus.interface.flet_interface.flet_utils import FletUtils
from pysaurus.interface.flet_interface.page.taskpage_utils import (
    NotificationCollector,
    NotificationRenderer,
)
from pysaurus.interface.flet_interface.page.videos_page import VideosPage


class TaskPage(ft.Column):
    def __init__(
        self,
        function: callable,
        arguments: Sequence,
        title=None,
        title_running="Working ...",
        title_done="Done!",
        auto_submit=False,
        on_submit=None,
    ):
        super().__init__()
        self.function = function
        self.arguments = arguments
        self.title_running = title_running
        self.title_done = title_done
        self.auto_submit = auto_submit
        self.submit_callback = on_submit or self.default_submit

        self.messages = ft.ListView(expand=1, padding=10)
        self.submit_button = ft.ElevatedButton(
            self.title_running, disabled=True, on_click=self.submit
        )
        self.notification_collector = NotificationCollector()
        self.notification_renderer = NotificationRenderer(self.notification_collector)
        self._collect_notification = Overridden(self.notification_collector)
        self._render_notification = Overridden(self.notification_renderer)

        if title is not None:
            self.controls.append(
                ft.Row([Title1(title)], alignment=ft.MainAxisAlignment.CENTER)
            )
        self.controls.append(
            ft.Container(
                self.messages,
                expand=1,
                border_radius=10,
                border=ft.border.all(1, ft.colors.GREY),
            )
        )
        self.controls.append(
            ft.Row([self.submit_button], alignment=ft.MainAxisAlignment.CENTER)
        )

    def did_mount(self):
        self.page.pubsub.subscribe(self.on_notification)
        self.function(*self.arguments)

    def will_unmount(self):
        self.page.pubsub.unsubscribe_all()
        print("task page will unmount")

    def on_notification(self, notification):
        assert isinstance(notification, Notification), notification
        self._collect_notification(notification)
        self._render_notifications()

    def _render_notifications(self):
        self.notification_renderer.clear()
        for i, notification in enumerate(self.notification_collector.notifications):
            self._render_notification(i, notification)

        done = self.notification_renderer.done
        controls = self.notification_renderer.controls

        if done:
            self.submit_button.text = self.title_done
            self.submit_button.disabled = False
            self.submit_button.update()
        else:
            trailing = ft.Text("...")
            controls.append(trailing)
        controls[-1].key = "trailing"

        self.messages.controls.clear()
        self.messages.controls.extend(controls)
        self.messages.scroll_to(key=controls[-1].key)
        self.messages.update()

    def default_submit(self):
        FletUtils.set_page(self.page, VideosPage())

    def submit(self, e):
        if self.submit_callback:
            self.submit_callback()
