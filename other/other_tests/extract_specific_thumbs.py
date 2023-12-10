import os

from other.other_tests.local_image_provider import LocalImageProvider
from pysaurus.core.components import AbsolutePath
from pysaurus.core.modules import ImageUtils
from tests.utils_testing import DB_INFO


def main():
    lip = LocalImageProvider()
    output_folder = AbsolutePath.join(
        os.path.join(os.path.dirname(__file__)), "ignored", lip.db_name, "selection"
    )
    output_folder.mkdir()
    for i, filename in enumerate(DB_INFO["filenames"]):
        blob = lip.thumb_manager.get_blob(AbsolutePath(filename))
        image = ImageUtils.from_blob(blob)
        output_image = AbsolutePath.join(output_folder, f"image{i + 1}.jpg")
        image.save(output_image.path)


if __name__ == "__main__":
    main()
