from typing import Dict, List

from pysaurus.core.classes import StringPrinter, ToDict


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

    def __init__(self, file_names: List):
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

    def __init__(self, video_errors: Dict[str, List[str]]):
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


class Done(End):
    __slots__ = ()


class Cancelled(End):
    __slots__ = ()


class DatabaseReady(End):
    __slots__ = ()


class ProfilingStart(Notification):
    __slots__ = ("name",)

    def __init__(self, title):
        # type: (str) -> None
        self.name = title

    def __str__(self):
        return f"ProfilingStart({self.name})"

    __repr__ = __str__


class ProfilingEnd(Notification):
    __slots__ = "name", "time"

    def __init__(self, name, duration):
        self.name = name
        self.time = str(duration)

    def __str__(self):
        return f"ProfilingEnded({self.name}, {self.time})"


class Profiled(ProfilingEnd):
    __slots__ = ()

    def __str__(self):
        return f"Profiled({self.name}, {self.time})"
