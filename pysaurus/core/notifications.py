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


class LogMessage(Notification):
    __slots__ = ['message']

    def __init__(self, message):
        self.message = message


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
        printer = utils.StringPrinter()
        printer.write(
            '%s: %d' % (type(self).__name__, sum(len(file_names) for file_names in self.folder_to_files.values())))
        for path in sorted(self.folder_to_files.keys()):
            printer.write('%d\t%s' % (len(self.folder_to_files[path]), path))
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
    __slots__ = ['total', 'not_found', 'valid']

    def __init__(self, total, not_found):
        self.total = total
        self.not_found = not_found
        self.valid = total - not_found


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


class InfoErrors(Notification):
    __slots__ = ['errors']

    def __init__(self, errors: list):
        self.errors = errors

    def __str__(self):
        printer = utils.StringPrinter()
        printer.write('%s: %d' % (type(self).__name__, len(self.errors)))
        for error in self.errors:
            printer.write('(error)')
            printer.write(error)
        return str(printer)


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


class ThumbnailErrors(InfoErrors):
    pass


class VideoThumbnailErrors(VideoInfoErrors):
    pass
