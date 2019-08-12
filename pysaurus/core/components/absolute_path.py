import os
import shutil
from typing import Union

from pysaurus.core.components.date_modified import DateModified
from pysaurus.core.utils.classes import System
from pysaurus.core.utils.constants import WINDOWS_PATH_PREFIX


class AbsolutePath(object):
    __slots__ = '__path',

    def __init__(self, path):
        # type: (str) -> None
        path = os.path.abspath(path)
        if len(path) >= 260 and System.is_windows() and not path.startswith(WINDOWS_PATH_PREFIX):
            path = '%s%s' % (WINDOWS_PATH_PREFIX, path)
        self.__path = path

    def is_standard(self):
        return not self.__path.startswith(WINDOWS_PATH_PREFIX)

    @property
    def standard_path(self):
        return self.__path[len(WINDOWS_PATH_PREFIX):] if self.__path.startswith(WINDOWS_PATH_PREFIX) else self.__path

    @property
    def path(self):
        return self.__path

    @property
    def title(self):
        basename = os.path.basename(self.__path)
        index_dot = basename.rfind('.')
        if index_dot == 0:
            return basename[1:]
        return basename if index_dot < 0 else basename[:index_dot]

    @property
    def extension(self):
        extension = os.path.splitext(self.__path)[1]
        return extension[1:].lower() if extension else ''

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
        return os.path.exists(self.__path)

    def isfile(self):
        return os.path.isfile(self.__path)

    def isdir(self):
        return os.path.isdir(self.__path)

    def listdir(self):
        return os.listdir(self.__path)

    def get_basename(self):
        return os.path.basename(self.__path)

    def get_directory(self):
        return AbsolutePath(os.path.dirname(self.__path))

    def in_directory(self, directory):
        directory = AbsolutePath.ensure(directory)
        if not directory.isdir():
            return False
        directory = directory.standard_path
        path = self.standard_path
        if len(directory) >= len(path):
            return False
        return path.startswith('%s%s' % (directory, os.sep))

    def get_date_modified(self):
        return DateModified(os.path.getmtime(self.__path))

    # not tested.
    def get_size(self):
        return os.path.getsize(self.__path)

    # not tested.
    def mkdir(self):
        os.makedirs(self.__path, exist_ok=True)
        if not os.path.isdir(self.__path):
            raise OSError("Unable to create a folder at path %s" % self.__path)

    def delete(self):
        if self.isfile():
            os.unlink(self.__path)
        else:
            shutil.rmtree(self.__path)
        if self.exists():
            raise OSError('Unable to delete path %s' % self.__path)

    def new_title(self, title):
        new_path = AbsolutePath.new_file_path(self.get_directory(), title, self.extension)
        if new_path.exists():
            raise OSError('Unable to rename (destination already exists) to', new_path)
        os.rename(self.__path, new_path.path)
        if self.exists():
            raise OSError('Unable to rename: source still exists:', self.__path)
        if not new_path.exists():
            raise OSError('Unable to rename to', new_path)
        return new_path

    def to_json(self):
        return str(self)

    @staticmethod
    def ensure(path):
        # type: (Union[str, AbsolutePath]) -> AbsolutePath
        return path if isinstance(path, AbsolutePath) else AbsolutePath(str(path))

    @classmethod
    def new_file_path(cls, folder_path, file_title, file_extension):
        """ Create a new file path with a folder, a file title and a file extension.
            Each piece will be converted to a string.
        :param folder_path: folder path.
        :param file_title: file title.
        :param file_extension: file extension.
        :return: a new AbsolutePath.
        :rtype: AbsolutePath
        """
        return AbsolutePath(os.path.join(str(folder_path), '%s.%s' % (file_title, file_extension)))

    @classmethod
    def join(cls, *args):
        """ Join pieces to create an absolute path (similar to os.path.join(...)).
        :param args: pieces of path to join (each converted to a string).
        :return: a new absolute path.
        :rtype: AbsolutePath
        """
        return AbsolutePath(os.path.join(*(str(piece) for piece in args)))
