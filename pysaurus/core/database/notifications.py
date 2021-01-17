from typing import Dict, List

from pysaurus.core.classes import StringPrinter
from pysaurus.core.notification import Notification


class UnusedThumbnails(Notification):
    __slots__ = ["removed"]

    def __init__(self, removed):
        # type: (int) -> None
        super().__init__()
        self.removed = removed


class VideosNotFoundRemoved(UnusedThumbnails):
    __slots__ = []


class CollectingFiles(Notification):
    __slots__ = ["folder"]

    def __init__(self, folder):
        super().__init__()
        self.folder = str(folder)


class FolderNotFound(CollectingFiles):
    __slots__ = []


class PathIgnored(CollectingFiles):
    __slots__ = []


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


class VideoJob(Notification):
    __slots__ = ["index", "parsed", "total"]

    def __init__(self, job_id, step, total):
        # type: (str, int, int) -> None
        super().__init__()
        self.index = job_id
        self.parsed = step
        self.total = total


class ThumbnailJob(VideoJob):
    __slots__ = []


class MiniatureJob(VideoJob):
    __slots__ = ()


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
    __props__ = __slots__

    def __init__(self, database):
        super().__init__()
        self.entries = database.nb_entries
        self.discarded = database.nb_discarded
        self.unreadable_not_found = len(database.get_source("unreadable", "not_found"))
        self.unreadable_found = len(database.get_source("unreadable", "found"))
        self.readable_not_found = len(database.get_source("readable", "not_found"))
        self.readable_found_without_thumbnails = len(
            database.get_source("readable", "found", "without_thumbnails")
        )
        self.valid = len(database.get_source("readable", "found", "with_thumbnails"))


class DatabaseSaved(DatabaseLoaded):
    __slots__ = []


class VideosToLoad(Notification):
    __slots__ = ["total"]

    def __init__(self, total):
        super().__init__()
        self.total = total


class ThumbnailsToLoad(VideosToLoad):
    __slots__ = []


class MiniaturesToLoad(VideosToLoad):
    __slots__ = ()


class NbMiniatures(VideosToLoad):
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
    __slots__ = []


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
    __slots__ = []


class DatabaseReady(Notification):
    __slots__ = ()


class Message(Notification):
    __slots__ = ("message",)

    def __init__(self, *message):
        super().__init__()
        with StringPrinter() as printer:
            printer.write(*message)
            self.message = str(printer)
