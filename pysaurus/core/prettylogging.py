import io
import logging
import pprint
import sys
from typing import Union

from pysaurus.core.classes import StringPrinter


def _printerr(*args, **kwargs):
    kwargs["file"] = sys.stderr
    return print(*args, **kwargs)


class PrettyLogging:
    _prefix = "║ "
    _suffix = " ║"
    _surrounding_size = len(_prefix) + len(_suffix)

    @classmethod
    def _can_log(cls, loglevel: Union[str, int]):
        return isinstance(loglevel, str) or loglevel >= logging.root.level

    @classmethod
    def _get_header(cls, loglevel: Union[str, int]):
        return loglevel if isinstance(loglevel, str) else logging.getLevelName(loglevel)

    @classmethod
    def _log(cls, loglevel: Union[int, str], *args, printer=_printerr):
        if args and cls._can_log(loglevel):
            with io.StringIO() as string_io:
                print(*args, end="", file=string_io)
                lines = [
                    line.rstrip("\r\n") for line in string_io.getvalue().splitlines()
                ]
            header = cls._get_header(loglevel)
            if len(lines) == 1:
                (content,) = lines
                head = f"{header}: " if header else ""
                printer(f"{head}{content}")
            else:
                max_line_length = (
                    max(len(line) for line in lines) + cls._surrounding_size
                )
                head = f" {header} " if header else ""
                req_length = max(max_line_length, len(head) + 4)
                printer(f"╔═{head}{'═' * (req_length - len(head) - 4)}═╗")
                for line in lines:
                    content = line.rjust(req_length - cls._surrounding_size)
                    printer(f"{cls._prefix}{content}{cls._suffix}")
                printer(f"╚{'═' * (req_length - 2)}╝")

    @classmethod
    def _format(cls, loglevel, *args) -> str:
        with StringPrinter() as printer:
            cls._log(loglevel, *args, printer=printer.write)
            return str(printer)

    @classmethod
    def debug(cls, *args):
        return cls._log(logging.DEBUG, *args)

    @classmethod
    def info(cls, *args):
        return cls._log(logging.INFO, *args)

    @classmethod
    def warning(cls, *args):
        return cls._log(logging.WARNING, *args)

    @classmethod
    def log(cls, *args):
        return cls._log("", *args, printer=print)

    @classmethod
    def format_debug(cls, *args) -> str:
        return cls._format(logging.DEBUG, *args)

    @classmethod
    def format_info(cls, *args) -> str:
        return cls._format(logging.INFO, *args)

    @classmethod
    def format_warning(cls, *args) -> str:
        return cls._format(logging.WARNING, *args)

    @classmethod
    def format(cls, *args) -> str:
        return cls._format("", *args)

    @classmethod
    def plog(cls, something):
        return cls.log(pprint.pformat(something))
