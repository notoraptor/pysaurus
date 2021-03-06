import os
import pathlib
import shutil
import subprocess
from datetime import datetime
from typing import Union

from pysaurus.core import constants
from pysaurus.core.constants import WINDOWS_PATH_PREFIX
from pysaurus.core.exceptions import UnsupportedOS, NotDirectoryError
from pysaurus.core.modules import FileSystem, System


class AbsolutePath(object):
    __slots__ = ("__path",)

    def __init__(self, path):
        # type: (str) -> None
        path = os.path.abspath(path)
        if (
            len(path) >= 260
            and System.is_windows()
            and not path.startswith(WINDOWS_PATH_PREFIX)
        ):
            path = "%s%s" % (WINDOWS_PATH_PREFIX, path)
        self.__path = path

    def is_standard(self):
        return not self.__path.startswith(WINDOWS_PATH_PREFIX)

    @property
    def standard_path(self):
        return (
            self.__path[len(WINDOWS_PATH_PREFIX) :]
            if self.__path.startswith(WINDOWS_PATH_PREFIX)
            else self.__path
        )

    @property
    def path(self):
        return self.__path

    @property
    def uri(self):
        return pathlib.Path(self.standard_path).as_uri()

    @property
    def title(self):
        """Get path title.

        For a directory, returns basename.
        For a file named `.ext`, returns `ext`.
        For a classic file `title.ext`, return `title`.
        """
        return os.path.basename(self.__path) if self.isdir() else self.file_title

    @property
    def file_title(self):
        """Get title for a file path.

        You can use it instead of `self.title` if you are already sure that
        this path leads to a file and not a directory.
        """
        basename = os.path.basename(self.__path)
        index_dot = basename.rfind(".")
        if index_dot == 0:
            return basename[1:]
        return basename if index_dot < 0 else basename[:index_dot]

    @property
    def extension(self):
        extension = os.path.splitext(self.__path)[1]
        return extension[1:].lower() if extension else ""

    def __str__(self):
        return self.standard_path

    def __repr__(self):
        return repr(self.standard_path)

    def __hash__(self):
        return hash(self.standard_path)

    def __eq__(self, other):
        return self.standard_path == other.standard_path

    def __lt__(self, other):
        return self.standard_path < other.standard_path

    def exists(self):
        return FileSystem.path.exists(self.__path)

    def isfile(self):
        return FileSystem.path.isfile(self.__path)

    def isdir(self):
        return FileSystem.path.isdir(self.__path)

    def listdir(self):
        return FileSystem.listdir(self.__path)

    def walk(self):
        return FileSystem.walk(self.__path)

    def get_basename(self):
        return os.path.basename(self.__path)

    def get_directory(self):
        return AbsolutePath(os.path.dirname(self.__path))

    def in_directory(self, directory, is_case_insensitive=None):
        directory = AbsolutePath.ensure(directory)
        if not directory.isdir():
            return False
        directory = directory.standard_path
        path = self.standard_path
        if is_case_insensitive:
            directory = directory.lower()
            path = path.lower()
        if len(directory) >= len(path):
            return False
        return path.startswith(
            "%s%s" % (directory, "" if directory.endswith(os.sep) else os.sep)
        )

    def get_date_modified(self):
        return DateModified(FileSystem.path.getmtime(self.__path))

    # not tested.
    def get_size(self):
        return FileSystem.path.getsize(self.__path)

    # not tested.
    def mkdir(self):
        FileSystem.makedirs(self.__path, exist_ok=True)
        if not FileSystem.path.isdir(self.__path):
            raise OSError("Unable to create a folder at path %s" % self.__path)
        return self

    def delete(self):
        if self.isfile():
            FileSystem.unlink(self.__path)
        elif self.isdir():
            shutil.rmtree(self.__path)
        if self.exists():
            raise OSError("Unable to delete path %s" % self.__path)

    def new_title(self, title):
        # type: (str) -> AbsolutePath
        new_path = FilePath(self.get_directory(), title, self.extension)
        if new_path.exists():
            raise OSError("Unable to rename (destination already exists) to", new_path)
        FileSystem.rename(self.__path, new_path.path)
        if self.exists():
            raise OSError("Unable to rename: source still exists:", self.__path)
        if not new_path.exists():
            raise OSError("Unable to rename to", new_path)
        return new_path

    def to_json(self):
        return str(self)

    def open(self):
        """Open path with default OS program."""
        if System.is_linux():
            subprocess.run(["xdg-open", self.__path])
        elif System.is_mac():
            subprocess.run(["open", self.__path])
        elif System.is_windows():
            if self.__path.startswith(WINDOWS_PATH_PREFIX):
                from pysaurus.core.native.windows import get_short_path_name

                path = get_short_path_name(self.standard_path)
                print("[Opening Windows short path]", path)
            else:
                path = self.__path
            FileSystem.startfile(path)
        else:
            raise UnsupportedOS(System.platform())
        return self

    def locate_file(self):
        if System.is_windows():
            command = 'explorer /select,"%s"' % self.__path
        elif System.is_mac():
            # TODO not tested
            command = ["open", "-R", self.__path]
        elif System.is_linux():
            # TODO not tested
            command = ["nautilus", self.__path]
        else:
            raise OSError(f"Unsupported OS: {System.platform()}")
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if stdout or stderr:
            return OSError(
                f"""Unable to locate file: {self.__path}
STDOUT: {stdout.strip()}
STDERR: {stderr.strip()}"""
            )
        return self.get_directory()

    def open_containing_folder(self):
        return self.locate_file() or self.get_directory().open()

    @staticmethod
    def ensure(path):
        # type: (Union[str, AbsolutePath]) -> AbsolutePath
        return path if isinstance(path, AbsolutePath) else AbsolutePath(str(path))

    @staticmethod
    def ensure_directory(path):
        path = AbsolutePath.ensure(path)
        if not path.isdir():
            raise NotDirectoryError(path)
        return path

    @classmethod
    def join(cls, *args):
        """Join pieces to create an absolute path (similar to os.path.join(...)).
        :param args: pieces of path to join (each converted to a string).
        :return: a new absolute path.
        :rtype: AbsolutePath
        """
        return AbsolutePath(os.path.join(*(str(piece) for piece in args)))


PathType = Union[AbsolutePath, str]


class FilePath(AbsolutePath):
    def __init__(self, folder_path, file_title, file_extension):
        # type: (PathType, str, str) -> None
        """Create a new file path with a folder, a file title and a file extension.
            Each piece will be converted to a string.
        :param folder_path: folder path.
        :param file_title: file title.
        :param file_extension: file extension.
        """
        super().__init__(
            os.path.join(str(folder_path), "%s.%s" % (file_title, file_extension))
        )


class DateModified:
    __slots__ = ("time",)

    def __init__(self, float_timestamp):
        self.time = float_timestamp

    def __str__(self):
        return datetime.fromtimestamp(self.time).strftime("%Y-%m-%d %H:%M:%S")

    def __hash__(self):
        return hash(self.time)

    def __eq__(self, other):
        return self.time == other.time

    def __lt__(self, other):
        return self.time < other.time

    def __ge__(self, other):
        return self.time >= other.time

    def to_json(self):
        return str(self)

    @property
    def day(self):
        return datetime.fromtimestamp(self.time).strftime("%Y-%m-%d")

    @staticmethod
    def now():
        return DateModified(datetime.now().timestamp())


class Duration(object):
    __slots__ = (
        "days",
        "hours",
        "minutes",
        "seconds",
        "microseconds",
        "total_microseconds",
    )

    def __init__(self, microseconds: Union[int, float]):
        if isinstance(microseconds, float):
            microseconds = round(microseconds)

        solid_seconds = microseconds // 1000000
        solid_minutes = solid_seconds // 60
        solid_hours = solid_minutes // 60

        self.days = solid_hours // 24
        self.hours = solid_hours % 24
        self.minutes = solid_minutes % 60
        self.seconds = solid_seconds % 60
        self.microseconds = microseconds % 1000000

        # Comparable duration is video duration round to microseconds.
        self.total_microseconds = microseconds

    def __hash__(self):
        return hash(self.total_microseconds)

    def __eq__(self, other):
        return self.total_microseconds == other.total_microseconds

    def __ne__(self, other):
        return self.total_microseconds != other.total_microseconds

    def __lt__(self, other):
        return self.total_microseconds < other.total_microseconds

    def __gt__(self, other):
        return self.total_microseconds > other.total_microseconds

    def __le__(self, other):
        return self.total_microseconds <= other.total_microseconds

    def __ge__(self, other):
        return self.total_microseconds >= other.total_microseconds

    def __str__(self):
        view = []
        if self.days:
            view.append("%02dd" % self.days)
        if self.hours:
            view.append("%02dh" % self.hours)
        if self.minutes:
            view.append("%02dm" % self.minutes)
        if self.seconds:
            view.append("%02ds" % self.seconds)
        if self.microseconds:
            view.append("%06dµs" % self.microseconds)
        return " ".join(view) if view else "00s"

    def to_json(self):
        return str(self)

    @classmethod
    def from_seconds(cls, seconds):
        return cls(seconds * 1_000_000)

    @classmethod
    def from_minutes(cls, minutes):
        return cls(minutes * 60_000_000)


class FileSize(object):
    __slots__ = ("__size", "__unit")

    def __init__(self, size):
        # type: (int) -> None
        self.__size = size
        self.__unit = constants.BYTES
        for unit in (
            constants.TERA_BYTES,
            constants.GIGA_BYTES,
            constants.MEGA_BYTES,
            constants.KILO_BYTES,
        ):
            if size // unit:
                self.__unit = unit
                break

    @property
    def value(self):
        return self.__size

    @property
    def nb_units(self):
        return self.__size / self.__unit

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return isinstance(other, FileSize) and self.value == other.value

    def __lt__(self, other):
        return isinstance(other, FileSize) and self.value < other.value

    def __str__(self):
        return "%s %s" % (
            round(self.nb_units, 2),
            constants.SIZE_UNIT_TO_STRING[self.__unit],
        )

    def to_json(self):
        return str(self)
