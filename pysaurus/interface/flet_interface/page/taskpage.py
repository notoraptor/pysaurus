"""
NB: Code is currently wrong, notably around progress bars.
"""

from typing import Dict, List, Sequence

import flet as ft

from pysaurus.core.classes import StringPrinter
from pysaurus.core.functions import string_to_pieces
from pysaurus.core.job_notifications import JobStep, JobToDo
from pysaurus.core.notifications import (
    Cancelled,
    DatabaseReady,
    Done,
    End,
    FinishedCollectingVideos,
    Message,
    MissingThumbnails,
    NbMiniatures,
    Notification,
    VideoInfoErrors,
    VideoThumbnailErrors,
)
from pysaurus.core.profiling import ProfilingEnd, ProfilingStart
from pysaurus.database.json_database_utils import DatabaseLoaded, DatabaseSaved
from pysaurus.interface.flet_interface.flet_utils import Title1


class ProgressionMonitoring:
    __slots__ = ("name", "total", "title", "channels")

    def __init__(self, notification: JobToDo):
        self.name = notification.name
        self.total = notification.total
        self.title = None
        self.channels = {}

    def collect(self, notification: JobStep):
        self.channels[notification.channel] = notification.step
        self.title = notification.title


class TaskPage(ft.Column):
    def __init__(
        self,
        page: ft.Page,
        function: callable,
        arguments: Sequence,
        title="Working ...",
        done_message="Done!",
    ):
        super().__init__()
        self.function = function
        self.arguments = arguments
        self.title = title
        self.done_message = done_message
        self.header = Title1(self.title)
        self.messages = ft.ListView(expand=1, padding=10)
        self.submit_button = ft.ElevatedButton(self.title, disabled=True)
        self.notifications: List[Notification] = []
        self.job_map: Dict[str, ProgressionMonitoring] = {}

        self.controls = [
            ft.Row([self.header], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(
                self.messages,
                expand=1,
                border_radius=10,
                border=ft.border.all(1, ft.colors.GREY),
            ),
            ft.Row([self.submit_button], alignment=ft.MainAxisAlignment.CENTER),
        ]

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

    def _collect_notification(self, notification: Notification):
        if isinstance(notification, JobToDo):
            assert notification.name not in self.job_map, (
                notification,
                self.job_map.keys(),
            )
            self.job_map[notification.name] = ProgressionMonitoring(notification)
            self.notifications.append(notification)
        elif isinstance(notification, JobStep):
            assert notification.name in self.job_map, (
                notification,
                self.job_map.keys(),
            )
            monitoring = self.job_map[notification.name]
            monitoring.collect(notification)
            # We collect JobStep in monitoring object, not in notifications list.
        else:
            self.notifications.append(notification)

    def _render_notifications(self):
        controls = []
        done = False
        for i, notification in enumerate(self.notifications):
            if type(notification) is Message:
                controls.append(ft.Markdown(f"**⚠** {notification.message}"))
            elif type(notification) is End:
                info = notification.message
                display = ft.Text("Ended." + (f" {info}" if info else ""))
                controls.append(display)
            elif isinstance(notification, DatabaseReady):
                done = True
                controls.append(ft.Text("Database open!"))
            elif isinstance(notification, Done):
                done = True
                controls.append(ft.Text("Done!"))
            elif isinstance(notification, Cancelled):
                done = True
                controls.append(ft.Text("Cancelled."))
            elif isinstance(notification, JobToDo):
                # Display job info
                if notification.title:
                    display = ft.Text(notification.title)
                elif notification.total:
                    display = ft.Text(
                        f"To load: {notification.total} {notification.name}"
                    )
                else:
                    display = ft.Text("To load: nothing!")
                controls.append(display)
                # Display job progression
                monitoring = self.job_map[notification.name]
                total = monitoring.total
                current = sum(monitoring.channels.values())
                percent = round(current * 100 / total)
                title = (
                    monitoring.title
                    if current and monitoring.title
                    else f"{current} done"
                )
                controls.append(
                    ft.Row(
                        [
                            ft.Text(f"{title} ({percent} %)", expand=3),
                            ft.ProgressBar(value=current / total, expand=7),
                        ]
                    )
                )
            elif isinstance(notification, JobStep):
                raise ValueError("Should not get a job step in collected notifications")
            elif isinstance(notification, (DatabaseSaved, DatabaseLoaded)):
                name = " ".join(string_to_pieces(type(notification).__name__))
                name = name[0].upper() + name[1:]
                controls.append(
                    ft.Text(
                        f"{name}: {notification.entries} entries, "
                        f"{notification.discarded} discarded, "
                        f"{notification.unreadable_not_found} unreadable not found, "
                        f"{notification.unreadable_found} unreadable found, "
                        f"{notification.readable_not_found} readable not found, "
                        f"{notification.readable_found_without_thumbnails} "
                        f"readable found without thumbnails, "
                        f"{notification.valid} valid"
                    )
                )
            elif isinstance(notification, FinishedCollectingVideos):
                controls.append(ft.Text(f"Collected {notification.count} file(s)"))
            elif isinstance(notification, ProfilingStart):
                controls.append(ft.Markdown(f"**PROFILING** {notification.name}"))
            elif isinstance(notification, ProfilingEnd):
                suffix = f"PROFILED** {notification.name} **TIME** {notification.time}"
                if (
                    i
                    and isinstance(self.notifications[i - 1], ProfilingStart)
                    and self.notifications[i - 1].name == notification.name
                ):
                    controls[-1] = ft.Markdown(f"**PROFILING / {suffix}")
                else:
                    controls.append(ft.Markdown(f"**{suffix}"))
            elif isinstance(notification, NbMiniatures):
                if notification.total:
                    controls.append(
                        ft.Text(f"{notification.total} miniature(s) saved.")
                    )
                else:
                    controls.append(ft.Text("No miniatures saved!"))
            elif isinstance(notification, MissingThumbnails):
                if notification.names:
                    with StringPrinter() as printer:
                        printer.write(
                            f"**Missing {len(notification.names)} thumbnail(s)**:"
                        )
                        printer.write("```")
                        for name in notification.names:
                            printer.write(name)
                        printer.write("```")
                        controls.append(ft.Markdown(str(printer)))
                else:
                    controls.append(ft.Text("No missing thumbnails!"))
            elif isinstance(notification, (VideoInfoErrors, VideoThumbnailErrors)):
                with StringPrinter() as printer:
                    printer.write(
                        f"**{len(notification.video_errors)} "
                        f"{' '.join(string_to_pieces(type(notification).__name__))}**:"
                    )
                    printer.write()
                    for name in sorted(notification.video_errors.keys()):
                        printer.write(f"`{name}`")
                        for error in notification.video_errors[name]:
                            printer.write(f"- `{error}`")
                    controls.append(ft.Markdown(str(printer)))
            else:
                controls.append(ft.Text(str(notification)))

        if done:
            self.header.value = self.done_message
            self.submit_button.text = self.done_message
            self.submit_button.disabled = False
            self.header.update()
            self.submit_button.update()
        else:
            trailing = ft.Text("...")
            controls.append(trailing)
        controls[-1].key = "trailing"

        self.messages.controls.clear()
        self.messages.controls.extend(controls)
        self.messages.scroll_to(key=controls[-1].key)
        self.messages.update()
