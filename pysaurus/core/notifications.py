from typing import Dict

from pysaurus.core.utils.classes import StringPrinter
from pysaurus.core.utils.functions import to_printable


class Notification(object):
    __slots__ = []

    def to_dict(self):
        return {name: getattr(self, name) for name in sorted(self.__slots__)}

    def __str__(self):
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('%s=%s' % (name, to_printable(getattr(self, name))) for name in sorted(self.__slots__)))


class ProfilingStart(Notification):
    __slots__ = ['name']

    def __init__(self, title):
        # type: (str) -> None
        self.name = title


class ProfilingEnd(Notification):
    __slots__ = ('name', 'time')

    def __init__(self, name, time):
        self.name = name
        self.time = str(time)


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

    def __init__(self, folder_to_files: dict):
        self.count = 0
        self.folder_to_count = {}
        for folder, file_names in folder_to_files.items():
            local_count = len(file_names)
            self.count += local_count
            self.folder_to_count[str(folder)] = local_count

    def __str__(self):
        printer = StringPrinter()
        printer.write('%s: %d' % (type(self).__name__, self.count))
        for folder, local_count in sorted(self.folder_to_count.items(), key=lambda couple: (-couple[1], couple[0])):
            printer.write('%d\t%s' % (local_count, folder))
        return str(printer)


class VideoJob(Notification):
    __slots__ = ['index', 'parsed', 'total']

    def __init__(self, job_id, step, total):
        # type: (int, int, int) -> None
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


class VideosLoaded(VideosToLoad):
    pass


class ThumbnailsToLoad(VideosToLoad):
    pass


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
