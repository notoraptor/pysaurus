from typing import Dict

from pysaurus.core.notification import Notification
from pysaurus.core.utils.classes import StringPrinter


class UnusedThumbnails(Notification):
    __slots__ = ['removed']

    def __init__(self, removed):
        # type: (int) -> None
        self.removed = removed


class VideosNotFoundRemoved(UnusedThumbnails):
    pass


class CollectingFiles(Notification):
    __slots__ = ['folder']

    def __init__(self, folder):
        self.folder = str(folder)


class FolderNotFound(CollectingFiles):
    pass


class PathIgnored(CollectingFiles):
    pass


class CollectedFiles(Notification):
    __slots__ = ['count', 'folder_to_count']
    count: int
    folder_to_count: Dict[str, int]

    def __init__(self, paths: list):
        self.count = len(paths)
        self.folder_to_count = {}
        for path in paths:
            directory = str(path.get_directory())
            if directory in self.folder_to_count:
                self.folder_to_count[directory] += 1
            else:
                self.folder_to_count[directory] = 1

    def __str__(self):
        printer = StringPrinter()
        printer.write('%s: %d' % (type(self).__name__, self.count))
        for folder, local_count in sorted(self.folder_to_count.items(), key=lambda couple: (-couple[1], couple[0])):
            printer.write('%d\t%s' % (local_count, folder))
        return str(printer)


class VideoJob(Notification):
    __slots__ = ['index', 'parsed', 'total']

    def __init__(self, job_id, step, total):
        # type: (str, int, int) -> None
        self.index = job_id
        self.parsed = step
        self.total = total


class ThumbnailJob(VideoJob):
    pass


class DatabaseLoaded(Notification):
    __slots__ = ['unreadable', 'not_found', 'valid', 'entries', 'found', 'thumbnails']

    def __init__(self, database):
        self.not_found = database.nb_not_found
        self.unreadable = database.nb_unreadable
        self.valid = database.nb_valid
        self.entries = database.nb_entries
        self.found = database.nb_found
        self.thumbnails = database.nb_thumbnails


class DatabaseSaved(DatabaseLoaded):
    pass


class VideosToLoad(Notification):
    __slots__ = ['total']

    def __init__(self, total):
        self.total = total


class ThumbnailsToLoad(VideosToLoad):
    pass


# Unused, sub-classed,
class MissingVideos(Notification):
    __slots__ = ['names']

    def __init__(self, file_names):
        self.names = [str(file_name) for file_name in file_names]

    def __str__(self):
        printer = StringPrinter()
        printer.write('%s: %d' % (type(self).__name__, len(self.names)))
        for name in sorted(self.names):
            printer.write('\t%s' % name)
        return str(printer)


class MissingThumbnails(MissingVideos):
    pass


class VideoInfoErrors(Notification):
    __slots__ = ['video_errors']

    def __init__(self, video_errors: dict):
        self.video_errors = {str(file_name): errors for file_name, errors in video_errors.items()}

    def __str__(self):
        printer = StringPrinter()
        printer.write('%s: %d' % (type(self).__name__, len(self.video_errors)))
        for file_name, errors in self.video_errors.items():
            printer.title(file_name)
            for video_error in errors:
                printer.write('\t%s' % video_error)
        return str(printer)


class VideoThumbnailErrors(VideoInfoErrors):
    pass
