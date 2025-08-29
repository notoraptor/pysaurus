from typing import Self

from pysaurus.core.classes import StringPrinter, ToDict
from pysaurus.core.functions import camel_case_to_snake_case


class Notification(ToDict):
    __slots__ = ()

    def describe(self) -> dict:
        return {
            "name": type(self).__name__,
            "notification": self.to_dict(),
            "message": str(self),
        }


class FinishedCollectingVideos(Notification):
    __slots__ = ("count",)

    def __init__(self, paths):
        super().__init__()
        self.count = len(paths)


class NbMiniatures(Notification):
    __slots__ = ("total",)

    def __init__(self, total):
        self.total = total


class MissingThumbnails(Notification):
    __slots__ = ("names",)

    def __init__(self, file_names: list):
        super().__init__()
        self.names = sorted(str(file_name) for file_name in file_names)

    def __str__(self):
        with StringPrinter() as printer:
            printer.write(f"{type(self).__name__}: {len(self.names)}")
            for name in sorted(self.names):
                printer.write(f"\t{name}")
            return str(printer)


class VideoInfoErrors(Notification):
    __slots__ = ("video_errors",)

    def __init__(self, video_errors: dict[str, list[str]]):
        super().__init__()
        self.video_errors = {
            str(file_name): sorted(errors) for file_name, errors in video_errors.items()
        }

    def __str__(self):
        with StringPrinter() as printer:
            printer.write(f"{type(self).__name__}: {len(self.video_errors)}")
            for file_name, errors in self.video_errors.items():
                printer.title(file_name)
                for video_error in errors:
                    printer.write(f"\t{video_error}")
            return str(printer)


class VideoThumbnailErrors(VideoInfoErrors):
    __slots__ = ()


class Message(Notification):
    __slots__ = ("message",)

    def __init__(self, *message):
        super().__init__()
        with StringPrinter() as printer:
            if message:
                printer.write(*message)
            self.message = str(printer)


class End(Message):
    __slots__ = ()

    def __str__(self):
        name = camel_case_to_snake_case(type(self).__name__).replace("_", " ")
        name = name[0].upper() + name[1:]
        return name + "!"


class Done(End):
    __slots__ = ()


class Cancelled(End):
    __slots__ = ()


class DatabaseReady(End):
    __slots__ = ()


class ProfilingStart(Notification):
    __slots__ = ("name",)

    def __init__(self, title: str):
        self.name = title

    def __str__(self):
        return f"ProfilingStart({self.name})"

    __repr__ = __str__


class ProfilingEnd(Notification):
    __slots__ = "name", "time", "inline"

    def __init__(self, name, duration, *, inline=False):
        self.name = name
        self.time = str(duration)
        self.inline = inline

    def with_inline(self, inline: bool) -> Self:
        return ProfilingEnd(self.name, self.time, inline=inline)

    def __str__(self):
        classname = "Profiled" if self.inline else "ProfilingEnded"
        return f"{classname}({self.name}, {self.time})"
