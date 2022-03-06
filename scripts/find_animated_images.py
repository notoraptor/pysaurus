import sys

from PIL import Image, UnidentifiedImageError

from pysaurus.core.components import AbsolutePath


def main():
    if len(sys.argv) != 2:
        return
    folder = AbsolutePath.ensure_directory(sys.argv[1])
    for basename in folder.listdir():
        try:
            path = AbsolutePath.join(folder, basename)
            if not path.isfile():
                continue
            image = Image.open(path.path)
            if image.is_animated:
                print(path)
        except UnidentifiedImageError:
            pass


if __name__ == "__main__":
    main()
