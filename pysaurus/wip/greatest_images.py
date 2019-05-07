import os
import shutil
import sys

from PIL import Image


def main():
    if len(sys.argv) != 4:
        return
    input_folder = os.path.abspath(sys.argv[1])
    output_folder = os.path.abspath(sys.argv[2])
    max_size = int(sys.argv[3])
    os.makedirs(output_folder, exist_ok=True)
    for file_name in os.listdir(input_folder):
        _, file_extension = os.path.splitext(file_name)
        if file_extension.lower() not in ('.jpg', '.jpeg', '.png'):
            continue
        absolute_file_path = os.path.join(input_folder, file_name)
        image = Image.open(absolute_file_path)
        if image.width > max_size or image.height > max_size:
            output_file_path = os.path.join(output_folder, file_name)
            print(absolute_file_path)
            shutil.copy(absolute_file_path, output_file_path)


if __name__ == '__main__':
    main()
