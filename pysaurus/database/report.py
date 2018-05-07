import textwrap

from pysaurus.utils import common
from pysaurus.utils.absolute_path import AbsolutePath


class CountFromDisk(object):
    __slots__ = 'collected', 'ignored'

    def __init__(self):
        self.collected, self.ignored = 0, 0


class CountLoadedFromDisk(object):
    __slots__ = 'errors', 'unloaded', 'updated', 'loaded'

    def __init__(self):
        self.errors, self.unloaded, self.updated, self.loaded = 0, 0, 0, 0


class DiskReport(object):
    __slots__ = ('folder_path', 'ignored', 'collected', 'errors', 'already_loaded', 'updated', 'loaded')

    def __init__(self, folder_path):
        self.folder_path = AbsolutePath.ensure(folder_path)
        self.collected = []
        self.ignored = []

        self.already_loaded = []
        self.errors = []
        self.updated = []
        self.loaded = []

    def __bool__(self):
        return any(bool(getattr(self, name)) for name in self.__slots__[1:])

    def __str__(self):
        string_pieces = []
        longest_printed_name_length = 0
        string_printer = common.StringPrinter(strip_right=False)
        for name in self.__slots__[1:]:
            value = getattr(self, name)
            value_length = value if isinstance(value, int) else len(value)
            if value_length:
                string_pieces.append((name, value_length))
                longest_printed_name_length = max(longest_printed_name_length, len(name))
        string_printer.write(self.__class__.__name__, end='')
        if longest_printed_name_length:
            string_printer.write(' (%s) {' % self.folder_path)
            string_format = '\t{:<%d}:\t{}' % (longest_printed_name_length + 1)
            for name, value_length in string_pieces:
                string_printer.write(string_format.format(name, value_length))
            string_printer.write('}', end='')
        else:
            string_printer.write(' (%s) {}' % self.folder_path, end='')
        return str(string_printer)


class DatabaseReport(object):
    __slots__ = ('disk', 'n_checked', 'errors', 'removed', 'not_found', 'n_loaded', 'n_saved')

    def __init__(self):
        self.n_checked = 0
        self.n_loaded = 0
        self.errors = []
        self.not_found = []
        self.removed = []
        self.n_saved = 0
        self.disk = {}  # type: dict{AbsolutePath, DiskReport}

    def __bool__(self):
        return (any(bool(getattr(self, name)) for name in self.__slots__[1:])
                or any(bool(disk_report) for disk_report in self.disk.values()))

    def __str__(self):
        string_pieces = []
        longest_printed_name_length = 0
        string_printer = common.StringPrinter(strip_right=False)
        for name in self.__slots__[1:]:
            value = getattr(self, name)
            value_length = value if isinstance(value, int) else len(value)
            if value_length:
                string_pieces.append((name, value_length))
                longest_printed_name_length = max(longest_printed_name_length, len(name))
        string_printer.write(self.__class__.__name__, end='')
        if longest_printed_name_length or self.disk:
            string_printer.write(' {')
            if longest_printed_name_length:
                string_format = '\t{:<%d}:\t{}' % (longest_printed_name_length + 1)
                for name, value_length in string_pieces:
                    string_printer.write(string_format.format(name, value_length))
            if self.disk:
                for key in sorted(self.disk.keys()):
                    string_printer.write(textwrap.indent(str(self.disk[key]), '\t'))
            string_printer.write('}', end='')
        else:
            string_printer.write(' {}')
        return str(string_printer)

    def count_from_disk(self):
        counter = CountFromDisk()
        for disk_report in self.disk.values():  # type: DiskReport
            counter.collected += len(disk_report.collected)
            counter.ignored += len(disk_report.ignored)
        return counter

    def count_loaded_from_disk(self):
        counter = CountLoadedFromDisk()
        for disk_report in self.disk.values():  # type: DiskReport
            counter.errors += len(disk_report.errors)
            counter.unloaded += len(disk_report.already_loaded)
            counter.updated += len(disk_report.updated)
            counter.loaded += len(disk_report.loaded)
        return counter
