from typing import Dict, List, Iterable, Optional

from pysaurus.core.classes import ToDict, StringPrinter


class Notification(ToDict):
    __slots__ = ()


class UnusedThumbnails(Notification):
    __slots__ = ["removed"]

    def __init__(self, removed):
        # type: (int) -> None
        super().__init__()
        self.removed = removed


class VideosNotFoundRemoved(UnusedThumbnails):
    __slots__ = ()


class CollectingFiles(Notification):
    __slots__ = ["folder"]

    def __init__(self, folder):
        super().__init__()
        self.folder = str(folder)


class FolderNotFound(CollectingFiles):
    __slots__ = ()


class PathIgnored(CollectingFiles):
    __slots__ = ()


class CollectedFiles(Notification):
    __slots__ = ["count", "folder_to_count"]
    count: int
    folder_to_count: Dict[str, int]

    def __init__(self, paths: list):
        super().__init__()
        self.count = len(paths)
        self.folder_to_count = {}
        for path in paths:
            directory = str(path.get_directory())
            if directory in self.folder_to_count:
                self.folder_to_count[directory] += 1
            else:
                self.folder_to_count[directory] = 1

    def __str__(self):
        with StringPrinter() as printer:
            printer.write("%s: %d" % (type(self).__name__, self.count))
            for folder, local_count in sorted(
                self.folder_to_count.items(), key=lambda couple: (-couple[1], couple[0])
            ):
                printer.write("%d\t%s" % (local_count, folder))
            return str(printer)


class FinishedCollectingVideos(Notification):
    __slots__ = ["count"]

    def __init__(self, paths):
        super().__init__()
        self.count = len(paths)


class NbMiniatures(Notification):
    __slots__ = ("total",)

    def __init__(self, total):
        self.total = total


class DatabaseLoaded(Notification):
    __slots__ = (
        "entries",
        "discarded",
        "unreadable_not_found",
        "unreadable_found",
        "readable_not_found",
        "valid",
        "readable_found_without_thumbnails",
    )

    def __init__(self, database):
        super().__init__()
        self.entries = database.nb_entries
        self.discarded = database.nb_discarded
        self.unreadable_not_found = len(database.get_videos("unreadable", "not_found"))
        self.unreadable_found = len(database.get_videos("unreadable", "found"))
        self.readable_not_found = len(database.get_videos("readable", "not_found"))
        self.readable_found_without_thumbnails = len(
            database.get_videos("readable", "found", "without_thumbnails")
        )
        self.valid = len(database.get_videos("readable", "found", "with_thumbnails"))


class DatabaseSaved(DatabaseLoaded):
    __slots__ = ()


# Unused, sub-classed.


class MissingVideos(Notification):
    __slots__ = ["names"]

    def __init__(self, file_names):
        super().__init__()
        self.names = sorted(str(file_name) for file_name in file_names)

    def __str__(self):
        with StringPrinter() as printer:
            printer.write("%s: %d" % (type(self).__name__, len(self.names)))
            for name in sorted(self.names):
                printer.write("\t%s" % name)
            return str(printer)


class MissingThumbnails(MissingVideos):
    __slots__ = ()


class VideoInfoErrors(Notification):
    __slots__ = ["video_errors"]

    def __init__(self, video_errors: Dict[str, List[str]]):
        super().__init__()
        self.video_errors = {
            str(file_name): sorted(errors) for file_name, errors in video_errors.items()
        }

    def __str__(self):
        with StringPrinter() as printer:
            printer.write("%s: %d" % (type(self).__name__, len(self.video_errors)))
            for file_name, errors in self.video_errors.items():
                printer.title(file_name)
                for video_error in errors:
                    printer.write("\t%s" % video_error)
            return str(printer)


class VideoThumbnailErrors(VideoInfoErrors):
    __slots__ = ()


class DatabaseReady(Notification):
    __slots__ = ()


class Message(Notification):
    __slots__ = ("message",)

    def __init__(self, *message):
        super().__init__()
        with StringPrinter() as printer:
            printer.write(*message)
            self.message = str(printer)


# Database changes.


class VideoDeleted(Notification):
    __slots__ = ("video",)

    def __init__(self, video):
        super().__init__()
        self.video = video


class FieldsModified(Notification):
    __slots__ = ("fields",)

    def __init__(self, properties: Iterable[str]):
        super().__init__()
        self.fields = set(properties)


class PropertiesModified(FieldsModified):
    __slots__ = ()


class JobToDo(Notification):
    __slots__ = "name", "total"

    def __init__(self, name: str, total: int):
        self.name = name
        self.total = total


class JobStep(Notification):
    __slots__ = "name", "channel", "step", "total"
    __slot_sorter__ = list

    def __init__(self, name: str, channel: Optional[str], step: int, total: int):
        self.name = name
        self.channel = channel
        self.step = step
        self.total = total


class JobNotifications:
    __slots__ = "name", "total", "notifier"

    def __init__(self, name: str, total: int, notifier):
        self.name = name
        self.total = total
        self.notifier = notifier
        self.todo()
        self.started()

    def todo(self):
        self.notifier.notify(JobToDo(self.name, self.total))

    def started(self):
        if self.total:
            self.notifier.notify(JobStep(self.name, None, 0, self.total))

    def progress(self, channel: Optional[str], channel_step: int, channel_size: int):
        self.notifier.notify(JobStep(self.name, channel, channel_step, channel_size))

    def __enter__(self):
        self.todo()
        self.started()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class _JobNotificationsFactory:
    __slots__ = ("name",)

    def __init__(self, name: str):
        self.name = name

    def __call__(self, total, notifier) -> JobNotifications:
        return JobNotifications(self.name, total, notifier)


class Jobs:
    videos = _JobNotificationsFactory("video")
    thumbnails = _JobNotificationsFactory("thumbnail")
    miniatures = _JobNotificationsFactory("miniature")
    group_computer = _JobNotificationsFactory("miniature group")
    gray_comparisons = _JobNotificationsFactory("miniature gray comparison")
    new_comparisons = _JobNotificationsFactory("new miniature comparison")
    native_comparisons = _JobNotificationsFactory("native comparison")
