from pysaurus.core.components import AbsolutePath
from pysaurus.core.constants import JPEG_EXTENSION
from pysaurus.core.informer import Informer
from pysaurus.core.modules import ImageUtils


def image_to_jpeg(input_path):
    path = AbsolutePath(input_path)
    output_path = AbsolutePath.file_path(
        path.get_directory(), path.title, JPEG_EXTENSION
    )
    ImageUtils.open_rgb_image(path.path).save(output_path.path)
    assert output_path.isfile()
    path.delete()


def compress_thumbnails_to_jpeg(job):
    notifier = Informer.default()
    path, job_id = job
    image_to_jpeg(path)
    notifier.progress(compress_thumbnails_to_jpeg, 1, 1, job_id)
