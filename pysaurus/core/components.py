import logging
import os
import pathlib
import shutil
import subprocess
from datetime import datetime
from typing import Self

from pysaurus.core import core_exceptions
from pysaurus.core.modules import FileSystem, System

logger = logging.getLogger(__name__)


class AbsolutePath:
    WINDOWS_PATH_PREFIX = "\\\\?\\"
    __slots__ = ("__path", "__len_prefix")

    def __init__(self, path: str):
        path = os.path.abspath(path)
        len_prefix = 0
        if path.startswith(self.WINDOWS_PATH_PREFIX):
            len_prefix = len(self.WINDOWS_PATH_PREFIX)
        elif len(path) >= 260 and System.is_windows():
            path = self.WINDOWS_PATH_PREFIX + path
            len_prefix = len(self.WINDOWS_PATH_PREFIX)
        self.__path = path
        self.__len_prefix = len_prefix

    @property
    def standard_path(self):
        return self.__path[self.__len_prefix :] if self.__len_prefix else self.__path

    @property
    def best_path(self):
        if System.is_windows():
            from pysaurus.core.native.windows import get_short_path_name

            return get_short_path_name(self.standard_path)
        return self.__path

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
    def extension(self) -> str:
        return os.path.splitext(self.__path)[1][1:].lower()

    def __str__(self):
        return self.standard_path

    def __repr__(self):
        return f"AbsolutePath({repr(self.standard_path)})"

    def __hash__(self):
        return hash(self.standard_path)

    def __eq__(self, other):
        return self.standard_path == other.standard_path

    def __lt__(self, other):
        return self.standard_path < other.standard_path

    def __len__(self):
        return len(self.__path)

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

    def get_date_modified(self):
        return Date(self.get_mtime())

    def get_mtime(self):
        return FileSystem.path.getmtime(self.__path)

    def get_drive_name(self):
        drive_name = os.path.splitdrive(self.standard_path)[0]
        if drive_name and not drive_name.endswith(os.path.sep):
            drive_name = drive_name + os.path.sep
        return drive_name

    def get_size(self):
        return FileSystem.path.getsize(self.__path)

    def mkdir(self):
        FileSystem.makedirs(self.__path, exist_ok=True)
        if not FileSystem.path.isdir(self.__path):
            raise NotADirectoryError(self.__path)
        return self

    def delete(self):
        if self.isfile():
            FileSystem.unlink(self.__path)
        elif self.isdir():
            shutil.rmtree(self.__path)
        if self.exists():
            raise FileExistsError(self.__path)

    def copy_file_to(self, dst):
        if not self.isfile():
            raise core_exceptions.NotAFileError(self)
        dst = self.ensure(dst)
        if dst.exists():
            raise FileExistsError(dst)
        shutil.copy(self.__path, dst.path)
        if not dst.isfile():
            raise FileNotFoundError(dst)

    def new_title(self, title: str) -> Self:
        new_path = AbsolutePath.file_path(self.get_directory(), title, self.extension)
        if new_path.exists():
            raise FileExistsError(new_path)
        FileSystem.rename(self.__path, new_path.path)
        if self.exists():
            raise FileExistsError(self.__path)
        if not new_path.exists():
            raise core_exceptions.NotAFileError(new_path)
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
            if self.__len_prefix:
                from pysaurus.core.native.windows import get_short_path_name

                path = get_short_path_name(self.standard_path)
                if path is None:
                    raise core_exceptions.NoShortPathError(self.__path)
                logger.debug(f"AbsolutePath: opening Windows short path {path}")
            else:
                path = self.__path
            FileSystem.startfile(path)
        else:
            raise core_exceptions.UnsupportedSystemError(System.platform())
        return self

    def locate_file_old(self):
        # NB: Windows: does not work with very long paths in exFAT file systems.
        if System.is_windows():
            command = f'explorer /select,"{self.__path}"'
        elif System.is_mac():
            # TODO not tested
            command = ["open", "-R", self.__path]
        elif System.is_linux():
            # TODO not tested
            command = ["nautilus", self.__path]
        else:
            raise core_exceptions.UnsupportedSystemError(System.platform())
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

    def locate_file(self):
        # https://pypi.org/project/show-in-file-manager/
        from showinfm import show_in_file_manager

        try:
            show_in_file_manager(self.standard_path)
        except Exception as exc:
            raise OSError(f"Error when locating {self.standard_path}") from exc
        return self.get_directory()

    def open_containing_folder(self):
        return self.locate_file() or self.get_directory().open()

    def assert_dir(self):
        if not self.isdir():
            raise NotADirectoryError(self)
        return self

    def assert_file(self):
        if not self.isfile():
            raise core_exceptions.NotAFileError(self)
        return self

    def read_binary_file(self):
        with open(self.__path, "rb") as file:
            return file.read()

    @classmethod
    def ensure(cls, path: str | Self) -> Self:
        return path if isinstance(path, AbsolutePath) else AbsolutePath(str(path))

    @staticmethod
    def map(iterable):
        return map(AbsolutePath.ensure, iterable)

    @staticmethod
    def ensure_directory(path):
        path = AbsolutePath.ensure(path)
        if not path.isdir():
            raise NotADirectoryError(path)
        return path

    @classmethod
    def join(cls, *args):
        """Join pieces to create an absolute path (similar to os.path.join(...)).
        :param args: pieces of path to join (each converted to a string).
        :return: a new absolute path.
        :rtype: AbsolutePath
        """
        return AbsolutePath(os.path.join(*(str(piece) for piece in args)))

    @classmethod
    def file_path(cls, folder_path, file_title, file_extension):
        """Create a new file path with a folder, a file title and a file extension.
            Each piece will be converted to a string.
        :param folder_path: folder path.
        :param file_title: file title.
        :param file_extension: file extension.
        """
        return cls(os.path.join(str(folder_path), f"{file_title}.{file_extension}"))


PathType = AbsolutePath | str


class Date:
    __slots__ = ("time",)

    def __init__(self, float_timestamp: float):
        self.time: float = float_timestamp

    def __str__(self):
        return datetime.fromtimestamp(self.time).strftime("%Y-%m-%d %H:%M:%S")

    def __hash__(self):
        return hash(self.time)

    def __float__(self):
        return self.time

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

    @property
    def year(self) -> int:
        return int(datetime.fromtimestamp(self.time).strftime("%Y"))

    @staticmethod
    def now():
        return Date(datetime.now().timestamp())
