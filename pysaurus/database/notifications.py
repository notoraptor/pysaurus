from abc import ABC
from io import StringIO

from pysaurus.database.report import DatabaseReport, DiskReport
from pysaurus.utils import common


class AbstractNotification(ABC):
    pass


class Message(AbstractNotification):
    __slots__ = '__message',

    def __init__(self, *args, **kwargs):
        string_buffer = StringIO()
        kwargs['file'] = string_buffer
        print(*args, **kwargs)
        self.__message = string_buffer.getvalue()
        string_buffer.close()

    def __str__(self):
        return self.__message


class DatabaseLoaded(AbstractNotification):
    __slots__ = 'database_report',

    def __init__(self, database_report: DatabaseReport):
        self.database_report = database_report

    def __str__(self):
        string_printer = common.StringPrinter()
        string_printer.write(self.database_report)
        if self.database_report.errors:
            len_title = string_printer.title('%d ERROR(S) WHILE LOADING DATABASE' % len(self.database_report.errors))
            line = '=' * len_title
            for path, traceback_string in self.database_report.errors:
                string_printer.write(path)
                string_printer.write(traceback_string)
                string_printer.write(line)
        return str(string_printer)


class VideosCollectedFromFolder(AbstractNotification):
    __slots__ = 'disk_report',

    def __init__(self, disk_report: DiskReport):
        self.disk_report = disk_report

    def __str__(self):
        return '(%d collected, %d ignored) %s' % (
            len(self.disk_report.collected), len(self.disk_report.ignored), self.disk_report.folder_path)


class VideosCollectedFromDisk(AbstractNotification):
    __slots__ = 'database_report',

    def __init__(self, database_report: DatabaseReport):
        self.database_report = database_report

    def __str__(self):
        count = self.database_report.count_from_disk()
        return '(%d collected, %d ignored)' % (count.collected, count.ignored)


class VideosAlreadyLoadedFromDisk(AbstractNotification):
    __slots__ = 'database_report',

    def __init__(self, database_report: DatabaseReport):
        self.database_report = database_report

    def __str__(self):
        count_collected = self.database_report.count_from_disk()
        count_loaded = self.database_report.count_loaded_from_disk()
        return '(%d/%d already loaded)' % (count_loaded.unloaded, count_collected.collected)


class StartedVideosLoading(AbstractNotification):
    def __str__(self):
        return '(loading videos from disk)'


class SteppingVideosLoading(AbstractNotification):
    __slots__ = 'count', 'total', 'job'

    def __init__(self, count: int, total: int, job=None):
        self.count = count
        self.total = total
        self.job = job

    def __str__(self):
        return '(%sloaded %d/%d videos)' % ('' if self.job is None else '[job %s] ' % self.job, self.count, self.total)


class FinishedVideosLoading(AbstractNotification):
    __slots__ = 'database_report'

    def __init__(self, database_report: DatabaseReport):
        self.database_report = database_report

    def __str__(self):
        count = self.database_report.count_loaded_from_disk()
        string_printer = common.StringPrinter()
        string_printer.write('(%d errors, %d unloaded, %d updated, %d loaded)' % (
            count.errors, count.unloaded, count.updated, count.loaded
        ))
        if count.errors:
            len_title = string_printer.title('%d ERROR(S) WHILE LOADING VIDEOS FROM DISK' % count.errors)
            line = '=' * len_title
            for disk_report in self.database_report.disk.values():
                for path, traceback_string in disk_report.errors:
                    string_printer.write(path)
                    string_printer.write(traceback_string)
                    string_printer.write(line)
        return str(string_printer)


class StartedDatabaseSaving(AbstractNotification):
    def __str__(self):
        return '(saving database)'


class StartedThumbnailsGenerator(AbstractNotification):
    def __str__(self):
        return '(generating thumbnails)'


class SteppingThumbnailsGenerator(AbstractNotification):
    __slots__ = 'count', 'total', 'job_name'

    def __init__(self, count: int, total: int, job_name=None):
        self.count = count
        self.total = total
        self.job_name = job_name

    def __str__(self):
        return '(%sgenerated %d/%d thumbnails)' % (
            '' if self.job_name is None else '[job %s] ' % self.job_name, self.count, self.total)


class FinishedThumbnailsGenerator(AbstractNotification):
    __slots__ = ('n_generated', 'n_total')

    def __init__(self, n_generated, n_total):
        self.n_generated = n_generated
        self.n_total = n_total

    def __str__(self):
        return '(finished generating %d/%d thumbnails)' % (self.n_generated, self.n_total)


class SavedDatabaseFile(AbstractNotification):
    def __str__(self):
        return '(saved database file)'


class SteppingDatabaseSaving(AbstractNotification):
    __slots__ = 'count', 'total', 'job'

    def __init__(self, count: int, total: int, job=None):
        self.count = count
        self.total = total
        self.job = job

    def __str__(self):
        return '(%ssaved %d/%d database video entries)' % (
            '' if self.job is None else '[job %s] ' % self.job, self.count, self.total)


class FinishedDatabaseSaving(AbstractNotification):
    __slots__ = 'count',

    def __init__(self, count: int):
        self.count = count

    def __str__(self):
        return '(Finished saving %d database video entries)' % self.count
