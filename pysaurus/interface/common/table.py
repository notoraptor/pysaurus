from typing import List

from pysaurus.core.utils.classes import StringPrinter


class Table:
    __slots__ = ('headers', 'lines')

    def __init__(self, headers, lines):
        # type: (List[str], List[List[str]]) -> None
        self.headers = headers
        self.lines = lines

    def __str__(self):
        printer = StringPrinter()
        header_sizes = [max(len(str(self.headers[i])), max(len(str(line[i])) for line in self.lines if line)) + 2
                        for i in range(len(self.headers))]
        printer.write(''.join(str(self.headers[i]).ljust(header_sizes[i]) for i in range(len(self.headers))))
        for line in self.lines:
            if line:
                printer.write(''.join(str(line[i]).ljust(header_sizes[i]) for i in range(len(self.headers))))
            else:
                printer.write()
        return str(printer)
