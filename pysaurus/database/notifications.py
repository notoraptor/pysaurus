import traceback

from pysaurus.database.notifier import AbstractNotification
from pysaurus.database.report import DatabaseReport, DiskReport
from pysaurus.utils import common


class LoadedDatabase(AbstractNotification):
    __slots__ = 'database_report',

    def __init__(self, database_report: DatabaseReport):
        self.database_report = database_report

    def __str__(self):
        string_printer = common.StringPrinter()
        string_printer.write(self.database_report)
        if self.database_report.errors:
            len_title = string_printer.title('%d ERROR(S) WHILE LOADING DATABASE' % len(self.database_report.errors))
            line = '=' * len_title
            for path, exception in self.database_report.errors:
                string_printer.write(path)
                traceback.print_tb(exception.__traceback__, file=string_printer.string_buffer)
                string_printer.write(line)
        return str(string_printer)


class ListedVideosFromFolder(AbstractNotification):
    __slots__ = 'disk_report',

    def __init__(self, disk_report: DiskReport):
        self.disk_report = disk_report

    def __str__(self):
        return '(%d collected, %d ignored) %s' % (
            len(self.disk_report.collected), len(self.disk_report.ignored), self.disk_report.folder_path)


class ListedVideosFromDisk(AbstractNotification):
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
    __slots__ = 'count', 'total'

    def __init__(self, count: int, total: int):
        self.count = count
        self.total = total

    def __str__(self):
        return '(loaded %d/%d videos)' % (self.count, self.total)


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
                for path, exception in disk_report.errors:
                    string_printer.write(path)
                    traceback.print_tb(exception.__traceback__, file=string_printer.string_buffer)
                    string_printer.write(type(exception).__name__)
                    string_printer.write(exception)
                    string_printer.write(line)
        return str(string_printer)
