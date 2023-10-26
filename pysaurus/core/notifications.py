from typing import Dict, Iterable, List

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

    def __init__(self, file_names: List[str]):
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


class Terminated(End):
    pass


class Done(Terminated):
    __slots__ = ()


class Cancelled(Terminated):
    __slots__ = ()


class DatabaseReady(Terminated):
    __slots__ = ()


class VideoDeleted(Notification):
    __slots__ = ("filename", "video_id")

    def __init__(self, filename: str, video_id: int):
        super().__init__()
        self.filename = filename
        self.video_id = video_id

    def __str__(self):
        return f"{type(self).__name__}({self.filename})"

    def to_dict(self, **extra):
        return {"video": str(self.filename)}


class FieldsModified(Notification):
    __slots__ = ("fields",)
    __props__ = ("modified",)

    modified = property(lambda self: sorted(self.fields))

    def __init__(self, properties: Iterable[str]):
        super().__init__()
        self.fields = set(properties)


class PropertiesModified(FieldsModified):
    __slots__ = ()


class DatabaseUpdated(Notification):
    __slots__ = ()
