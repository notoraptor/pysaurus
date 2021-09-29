from pysaurus.core.components import AbsolutePath
from pysaurus.core.constants import THUMBNAIL_EXTENSION
from pysaurus.core.modules import FNV64


def generate_thumb_name(file_name):
    # type: (AbsolutePath) -> str
    return FNV64.hash(file_name.standard_path)


def generate_thumb_path(folder, thumb_name):
    # type: (AbsolutePath, str) -> AbsolutePath
    return AbsolutePath.file_path(folder, thumb_name, THUMBNAIL_EXTENSION)
