from pysaurus.core import utils


def _wrap(element):
    if isinstance(element, str):
        if '"' in element:
            return "'%s'" % element
        return '"%s"' % element
    return element


class Notification(object):
    __slots__ = []

    def __str__(self):
        valid_attribute_names = list(sorted(name for name in dir(self)
                                            if not name.startswith('_')
                                            and not callable(getattr(self, name))))
        return '%s(%s)' % (
            type(self).__name__,
            ', '.join('%s=%s' % (name, _wrap(getattr(self, name))) for name in valid_attribute_names))


class UnusedThumbnails(Notification):
    __slots__ = ['removed']

    def __init__(self, removed):
        self.removed = removed


class CollectingFiles(Notification):
    __slots__ = ['folder']

    def __init__(self, folder):
        self.folder = folder


class FolderNotFound(CollectingFiles):
    pass


class FolderIgnored(CollectingFiles):
    pass


class CollectedFiles(Notification):
    __slots__ = ['folder_to_files']

    def __init__(self, folder_to_files: dict):
        self.folder_to_files = folder_to_files

    def __str__(self):
        total_count = 0
        folder_to_count = []
        for folder, file_names in self.folder_to_files.items():
            local_count = len(file_names)
            total_count += local_count
            folder_to_count.append((folder, local_count))
        folder_to_count.sort(key=lambda couple: (-couple[1], couple[0]))
        printer = utils.StringPrinter()
        printer.write(
            '%s: %d' % (type(self).__name__, total_count))
        for folder, local_count in folder_to_count:
            printer.write('%d\t%s' % (local_count, folder))
        return str(printer)


class VideoJob(Notification):
    __slots__ = ['index', 'parsed', 'total']

    def __init__(self, job_id, step, total):
        self.index = job_id
        self.parsed = step
        self.total = total


class ThumbnailJob(VideoJob):
    pass


class DatabaseLoaded(Notification):
    __slots__ = ['total', 'not_found', 'valid', 'unreadable']

    def __init__(self, total, not_found, unreadable):
        self.total = total
        self.not_found = not_found
        self.unreadable = unreadable
        self.valid = total - not_found - unreadable


class DatabaseSaved(Notification):
    __slots__ = ['total']

    def __init__(self, total):
        self.total = total


class VideosToLoad(DatabaseSaved):
    pass


class VideosLoaded(VideosToLoad):
    pass


class ThumbnailsToLoad(VideosToLoad):
    pass


class MissingVideos(Notification):
    __slots__ = ['names']

    def __init__(self, file_names):
        self.names = file_names

    def __str__(self):
        printer = utils.StringPrinter()
        printer.write('%s: %d' % (type(self).__name__, len(self.names)))
        for name in sorted(self.names):
            printer.write('\t%s' % name)
        return str(printer)


class MissingThumbnails(MissingVideos):
    pass


class VideoInfoErrors(Notification):
    __slots__ = ['video_errors']

    def __init__(self, video_errors: dict):
        self.video_errors = video_errors

    def __str__(self):
        printer = utils.StringPrinter()
        printer.write('%s: %d' % (type(self).__name__, len(self.video_errors)))
        for file_name in self.video_errors:
            printer.title(file_name)
            for video_error in self.video_errors[file_name]:
                printer.write('\t%s' % video_error)
        return str(printer)


class VideoThumbnailErrors(VideoInfoErrors):
    pass
