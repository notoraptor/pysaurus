from typing import Any, Iterable, List, Sequence

from other.toolsaurus.functions import class_get_field_title
from pysaurus.core.classes import StringPrinter


class Table:
    __slots__ = ("headers", "lines")

    def __init__(self, headers, lines):
        # type: (List[str], List[Sequence[Any]]) -> None
        self.headers = headers
        self.lines = lines

    def append(self, *columns):
        assert len(columns) == len(self.headers)
        self.lines.append(columns)

    def __str__(self):
        header_sizes = [
            max(
                len(str(self.headers[i])),
                max([len(str(line[i])) for line in self.lines if line] + [0]),
            )
            + 2
            for i in range(len(self.headers))
        ]
        with StringPrinter() as printer:
            printer.write(
                "".join(
                    str(self.headers[i]).ljust(header_sizes[i])
                    for i in range(len(self.headers))
                )
            )
            for line in self.lines:
                if line:
                    printer.write(
                        "".join(
                            str(line[i]).ljust(header_sizes[i])
                            for i in range(len(self.headers))
                        )
                    )
                else:
                    printer.write()
            return str(printer)


class Column(list):
    def __str__(self):
        with StringPrinter() as printer:
            for line in self:
                printer.write(line)
            return str(printer)


def to_table(elements: Iterable, element_type: type, fields: Sequence[str]):
    headers = [
        class_get_field_title(element_type, field) if field else "" for field in fields
    ]
    lines = [
        [getattr(element, field) if field else "" for field in fields]
        for element in elements
    ]
    return Table(headers, lines)


def to_column(lines: Iterable):
    return Column(lines)
