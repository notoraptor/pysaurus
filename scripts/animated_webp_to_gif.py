import sys

from PIL import Image

from pysaurus.core.components import AbsolutePath


def main():
    if len(sys.argv) != 2:
        return
    path = AbsolutePath(sys.argv[1]).assert_file()
    assert path.extension.lower() == "webp"
    image = Image.open(path.path)
    image.info.pop("background", None)
    assert image.is_animated
    output_path = AbsolutePath.join(path.get_directory(), f"{path.title}.gif")
    image.save(output_path.path, "gif", save_all=True, optimize=False)
    print(output_path)


if __name__ == "__main__":
    main()
