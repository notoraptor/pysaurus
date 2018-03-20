import os


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
        return hash(self.path)

    def __eq__(self, other):
        return self.path == other.path

    def __lt__(self, other):
        return self.path < other.path

    def exists(self):
        return os.path.exists(self.__path)

    def isfile(self):
        return os.path.isfile(self.__path)

    def isdir(self):
        return os.path.isdir(self.__path)

    def get_date_modified(self):
        return os.path.getmtime(self.path)

    def listdir(self):
        return os.listdir(self.path)

    def mkdir(self):
        os.mkdir(self.path)
        assert os.path.exists(self.path) and os.path.isdir(self.path)

    @classmethod
    def new_file_path(cls, folder_path, file_title, file_extension):
        return AbsolutePath(os.path.join(str(folder_path), '%s.%s' % (file_title, file_extension)))

    @classmethod
    def join(cls, *args):
        return AbsolutePath(os.path.join(*(str(piece) for piece in args)))
