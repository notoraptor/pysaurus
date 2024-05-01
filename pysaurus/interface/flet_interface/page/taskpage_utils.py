from typing import Dict, List

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


class NotificationCollector:
    __slots__ = ("notifications", "job_map")

    def __init__(self):
        self.notifications: List[Notification] = []
        self.job_map: Dict[str, ProgressionMonitoring] = {}

    def on_job_to_do(self, notification: JobToDo):
        assert notification.name not in self.job_map, (
            notification,
            self.job_map.keys(),
        )
        self.job_map[notification.name] = ProgressionMonitoring(notification)
        self.notifications.append(notification)

    def on_job_step(self, notification: JobStep):
        assert notification.name in self.job_map, (notification, self.job_map.keys())
        monitoring = self.job_map[notification.name]
        monitoring.collect(notification)
        # We collect JobStep in monitoring object, not in notifications list.

    def on(self, notification: Notification):
        self.notifications.append(notification)


class NotificationRenderer:
    __slots__ = ("collector", "controls", "done")

    def __init__(self, collector: NotificationCollector):
        self.collector = collector
        self.controls: List[ft.Control] = []
        self.done = False

    @property
    def notifications(self):
        return self.collector.notifications

    @property
    def job_map(self):
        return self.collector.job_map

    def clear(self):
        self.controls.clear()
        self.done = False

    def on_message(self, i: int, notification: Message):
        self.controls.append(ft.Markdown(f"**⚠** {notification.message}"))

    def on_end(self, i: int, notification: End):
        info = notification.message
        display = ft.Text("Ended." + (f" {info}" if info else ""))
        self.controls.append(display)

    def on_database_ready(self, i: int, notification: DatabaseReady):
        self.done = True
        self.controls.append(ft.Text("Database open!"))

    def on_done(self, i: int, notification: Done):
        self.done = True
        self.controls.append(ft.Text("Done!"))

    def on_cancelled(self, i: int, notification: Cancelled):
        self.done = True
        self.controls.append(ft.Text("Cancelled."))

    def on_job_to_do(self, i: int, notification: JobToDo):
        # Display job info
        if notification.title:
            display = ft.Text(notification.title)
        elif notification.total:
            display = ft.Text(f"To load: {notification.total} {notification.name}")
        else:
            display = ft.Text("To load: nothing!")
        self.controls.append(display)
        # Display job progression
        monitoring = self.job_map[notification.name]
        total = monitoring.total
        current = sum(monitoring.channels.values())
        percent = round(current * 100 / total)
        title = monitoring.title if current and monitoring.title else f"{current} done"
        self.controls.append(
            ft.Row(
                [
                    ft.Text(f"{title} ({percent} %)", expand=3),
                    ft.ProgressBar(value=current / total, expand=7),
                ]
            )
        )

    def on_job_step(self, i: int, notification: JobStep):
        raise ValueError("Should not get a job step in collected notifications")

    def on_database_loaded(self, i: int, notification: DatabaseLoaded):
        name = " ".join(string_to_pieces(type(notification).__name__))
        name = name[0].upper() + name[1:]
        self.controls.append(
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

    def on_database_saved(self, i: int, notification: DatabaseSaved):
        return self.on_database_loaded(i, notification)

    def on_finished_collecting_videos(
        self, i: int, notification: FinishedCollectingVideos
    ):
        self.controls.append(ft.Text(f"Collected {notification.count} file(s)"))

    def on_profiling_start(self, i: int, notification: ProfilingStart):
        self.controls.append(ft.Markdown(f"**PROFILING** {notification.name}"))

    def on_profiling_end(self, i: int, notification: ProfilingEnd):
        suffix = f"PROFILED** {notification.name} **TIME** {notification.time}"
        if (
            i
            and isinstance(self.notifications[i - 1], ProfilingStart)
            and self.notifications[i - 1].name == notification.name
        ):
            self.controls[-1] = ft.Markdown(f"**PROFILING / {suffix}")
        else:
            self.controls.append(ft.Markdown(f"**{suffix}"))

    def on_nb_miniatures(self, i: int, notification: NbMiniatures):
        if notification.total:
            self.controls.append(ft.Text(f"{notification.total} miniature(s) saved."))
        else:
            self.controls.append(ft.Text("No miniatures saved!"))

    def on_missing_thumbnails(self, i: int, notification: MissingThumbnails):
        if notification.names:
            with StringPrinter() as printer:
                printer.write(f"**Missing {len(notification.names)} thumbnail(s)**:")
                printer.write("```")
                for name in notification.names:
                    printer.write(name)
                printer.write("```")
                self.controls.append(
                    ft.Markdown(
                        str(printer),
                        extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
                        code_style=ft.TextStyle(font_family="Roboto Mono"),
                    )
                )
        else:
            self.controls.append(ft.Text("No missing thumbnails!"))

    def on_video_info_errors(self, i: int, notification: VideoInfoErrors):
        with StringPrinter() as printer:
            printer.write(
                f"**{len(notification.video_errors)} "
                f"{' '.join(string_to_pieces(type(notification).__name__))}**:"
            )
            printer.write()
            for name in sorted(notification.video_errors.keys()):
                printer.write("```")
                printer.write(f"{name}")
                for error in notification.video_errors[name]:
                    printer.write(f"    {error}")
                printer.write("```")
            self.controls.append(
                ft.Markdown(
                    str(printer),
                    extension_set=ft.MarkdownExtensionSet.GITHUB_FLAVORED,
                    code_style=ft.TextStyle(font_family="Roboto Mono"),
                )
            )

    def on_video_thumbnail_errors(self, i: int, notification: VideoThumbnailErrors):
        return self.on_video_info_errors(i, notification)

    def on(self, i: int, notification: Notification):
        self.controls.append(ft.Text(str(notification)))
