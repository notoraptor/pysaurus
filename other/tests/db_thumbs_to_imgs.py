import os

from tqdm import tqdm

from other.tests.utils_testing import LocalImageProvider
from pysaurus.core.components import AbsolutePath


class NameUniquer:
    __slots__ = ("seen",)

    def __init__(self):
        self.seen = set()

    def __call__(self, name: str) -> str:
        number = 0
        base = name
        while True:
            if base in self.seen:
                base = f"{name}_{number}"
                number += 1
            else:
                self.seen.add(base)
                return base


def main():
    uniquer = NameUniquer()
    imp = LocalImageProvider()
    output_folder = AbsolutePath.join(os.path.dirname(__file__), "ignored", imp.db_name)
    if output_folder.exists():
        assert output_folder.isdir()
    else:
        output_folder.mkdir()
    with tqdm(total=imp.count(), desc="Save thumbnails on disk") as pbar:
        for filename, image in imp.items():
            filename = AbsolutePath(filename)
            title = uniquer(filename.title)
            output_filename = AbsolutePath.join(output_folder, f"{title}.jpg")
            image.save(output_filename.path)
            pbar.update(1)


if __name__ == "__main__":
    main()
