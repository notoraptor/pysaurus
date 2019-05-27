import os
import platform
import shutil

from pysaurus.core.constants import WINDOWS_PATH_PREFIX


class AbsolutePath(object):

    def __init__(self, path: str):
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        if len(path) >= 260 and platform.system() == 'Windows' and not path.startswith(WINDOWS_PATH_PREFIX):
            path = '%s%s' % (WINDOWS_PATH_PREFIX, path)
        last_index_of_separator = path.rfind(os.path.sep)
        last_index_of_dot = -1 if last_index_of_separator < 0 else path.rfind('.', last_index_of_separator)
        index_title_start = 0 if last_index_of_separator < 0 else (last_index_of_separator + 1)
        index_title_end = len(path) if last_index_of_dot < 0 else last_index_of_dot
        self.__path = path
        self.__title = self.__path[index_title_start:index_title_end]
        self.__extension = self.__path[(index_title_end + 1):]

    path = property(lambda self: self.__path)
    title = property(lambda self: self.__title)
    extension = property(lambda self: self.__extension)

    def __str__(self):
        return self.__path

    def __hash__(self):
        return hash(self.__path)

    def __eq__(self, other):
        return self.__path == other.path

    def __lt__(self, other):
        return self.__path < other.path

    def exists(self):
        return os.path.exists(self.__path)

    def isfile(self):
        return os.path.isfile(self.__path)

    def isdir(self):
        return os.path.isdir(self.__path)

    def listdir(self):
        return os.listdir(self.__path)

    def get_basename(self):
        return '%s.%s' % (self.__title, self.__extension)

    def get_directory(self):
        return AbsolutePath(os.path.dirname(self.__path))

    def in_directory(self, directory):
        directory = AbsolutePath.ensure(directory)
        if not directory.isdir():
            return False
        directory = directory.path
        path = self.path
        if directory.startswith(WINDOWS_PATH_PREFIX):
            directory = directory[len(WINDOWS_PATH_PREFIX):]
        if path.startswith(WINDOWS_PATH_PREFIX):
            path = path[len(WINDOWS_PATH_PREFIX):]
        if len(directory) >= len(path):
            return False
        return path.startswith('%s%s' % (directory, os.sep))

    # not tested.
    def get_date_modified(self):
        return os.path.getmtime(self.__path)

    # not tested.
    def get_size(self):
        return os.path.getsize(self.__path)

    # not tested.
    def mkdir(self):
        os.makedirs(self.__path, exist_ok=True)
        if not os.path.isdir(self.__path):
            raise OSError("Unable to create a folder at path %s" % self.__path)

    # not tested.
    def delete(self):
        if self.isfile():
            os.unlink(self.__path)
        else:
            shutil.rmtree(self.__path)
        if self.exists():
            raise OSError('Unable to delete path %s' % self.__path)

    @classmethod
    def ensure(cls, path):
        """ Return path if it's already an AbsolutePath object, else convert it to an AbsolutePath object.
        :param path: path to check.
        :return: an AbsolutePath object.
        :rtype: AbsolutePath
        """
        if not isinstance(path, cls):
            path = cls(str(path))
        return path

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
