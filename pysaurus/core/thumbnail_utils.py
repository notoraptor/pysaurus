from pysaurus.core import utils
from pysaurus.core.absolute_path import AbsolutePath
from pysaurus.core.constants import THUMBNAIL_EXTENSION


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
