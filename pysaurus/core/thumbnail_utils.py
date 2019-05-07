from pysaurus.core import utils
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.utils import StringPrinter

THUMBNAIL_EXTENSION = 'png'


class VideoThumbnailResult:
    __slots__ = ('done', 'errors')

    def __init__(self, *, done, errors):
        self.done = bool(done)
        self.errors = set(errors)

    def __str__(self):
        printer = StringPrinter()
        printer.write('Thumbnail(')
        for field_name in sorted(self.__slots__):
            printer.write('\t%s: %s' % (field_name, getattr(self, field_name)))
        printer.write(')')
        return str(printer)


class ThumbnailStrings:

    @staticmethod
    def generate_name(file_name: AbsolutePath):
        return utils.Whirlpool.hash(file_name.path)

    @staticmethod
    def generate_path(folder: AbsolutePath, file_name: AbsolutePath):
        return AbsolutePath.new_file_path(folder, utils.Whirlpool.hash(file_name.path), THUMBNAIL_EXTENSION)

    @staticmethod
    def generate_path_from_name(folder: AbsolutePath, thumb_name: str):
        return AbsolutePath.new_file_path(folder, thumb_name, THUMBNAIL_EXTENSION)
