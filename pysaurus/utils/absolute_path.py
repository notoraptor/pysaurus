import os
import shutil


class AbsolutePath(object):

    def __init__(self, path):
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        last_index_of_separator = path.rindex(os.sep)
        last_index_of_dot = len(path)
        for index, character in enumerate(reversed(path)):
            if character == '.':
                if len(path) - 1 - index > last_index_of_separator:
                    last_index_of_dot = len(path) - 1 - index
                break
        self.__path = path
        self.__title = self.__path[(last_index_of_separator + 1):last_index_of_dot]
        self.__extension = self.__path[(last_index_of_dot + 1):]

    path = property(lambda self: self.__path)
    title = property(lambda self: self.__title)
    extension = property(lambda self: self.__extension)
    basename = property(lambda self: '%s.%s' % (self.__title, self.__extension))

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

    def get_date_modified(self):
        return os.path.getmtime(self.__path)

    def get_size(self):
        return os.path.getsize(self.__path)

    def get_dirname(self):
        return AbsolutePath(os.path.dirname(self.__path))

    def listdir(self):
        return os.listdir(self.__path)

    def mkdir(self):
        os.mkdir(self.__path)
        assert os.path.exists(self.__path) and os.path.isdir(self.__path)

    def delete(self):
        if self.isfile():
            os.unlink(self.__path)
        else:
            shutil.rmtree(self.__path)

    @classmethod
    def ensure(cls, path):
        if not isinstance(path, cls):
            path = cls(str(path))
        return path

    @classmethod
    def new_file_path(cls, folder_path, file_title, file_extension):
        return AbsolutePath(os.path.join(str(folder_path), '%s.%s' % (file_title, file_extension)))

    @classmethod
    def join(cls, *args):
        return AbsolutePath(os.path.join(*(str(piece) for piece in args)))
