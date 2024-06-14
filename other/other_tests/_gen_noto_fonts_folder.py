import os

from pysaurus.core.components import AbsolutePath
from resource.fonts import FOLDER_NOTO


def main():
    output_folder = AbsolutePath(FOLDER_NOTO)
    if output_folder.isdir():
        print("Folder already exist.")
        return
    output_folder.mkdir()

    fonts_folder = (
        r"C:\Users\notoraptor-desktop\Downloads\notofonts.github.io-main\fonts"
    )
    assert os.path.isdir(fonts_folder)
    count = 0
    for name in os.listdir(fonts_folder):
        font_folder = os.path.join(fonts_folder, name)
        if os.path.isdir(font_folder):
            font_name = f"{name}-Regular.ttf"
            font_path = os.path.join(font_folder, "unhinted", "ttf", font_name)
            assert os.path.isfile(font_path)
            print(name)
            count += 1
            AbsolutePath(font_path).copy_file_to(
                AbsolutePath.join(output_folder, font_name)
            )
    print(count)


if __name__ == "__main__":
    main()
