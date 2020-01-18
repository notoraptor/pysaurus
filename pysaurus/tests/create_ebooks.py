import argparse
from pysaurus.core.components import AbsolutePath, FilePath
from pysaurus.core.modules import ImageUtils
from pysaurus.core.functions import timestamp_microseconds
import re
import sys
from typing import List
import zipfile
import tempfile

TEMP_DIR = tempfile.gettempdir()

REGEX_NUMBER = re.compile(r'[0-9]+')
SUPPORTED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def fatal_error(log_file, path, message):
    print('[ERROR](%s): %s' % (path, message), file=log_file)


def info(log_file, path, message):
    print('[INFO](%s): %s' % (path, message), file=log_file)


def message(log_file, theme, path, message):
    print('[%s](%s): %s' % (theme, path, message), file=log_file)


class Converter:
    def __init__(self, args):
        self.input_folder = AbsolutePath(args.input)
        self.output_folder = AbsolutePath(args.output)
        log_file_path = args.log
        self.file = None
        if log_file_path:
            self.file = open(log_file_path, 'w', encoding='utf-8')
        try:
            self.visit(self.input_folder, self.file or sys.stdout)
        finally:
            if self.file:
                self.file.close()

    def convert_image(self, log_file, input_image: AbsolutePath):
        if input_image.extension == 'png':
            return input_image
        output_image = FilePath(input_image.get_directory(), input_image.title, 'png')
        if not output_image.isfile():
            image = ImageUtils.open_rgb_image(input_image.path)
            ImageUtils.save_rgb_image(*image.size, image.getdata(), output_image.path)
            assert output_image.isfile()
            message(log_file, 'CONVERTED', input_image.get_directory(), '%s => %s' % (input_image.get_basename(), output_image.get_basename()))
        return output_image

    def convert_to_ebook(self, directory, files, log_file):
        # type: (AbsolutePath, List[AbsolutePath], object) -> None
        to_update = False
        convert_images = len({file.extension for file in files}) != 1
        if convert_images:
            for input_file in files:
                output_file = self.convert_image(log_file, input_file)
                to_update = to_update or output_file != input_file

        upper_directory = directory.get_directory()
        output_directory = AbsolutePath(upper_directory.path.replace(self.input_folder.path, self.output_folder.path))
        output_ebook = FilePath(output_directory, directory.title, 'cbz')
        if output_ebook.isfile() and output_ebook.get_size() > 1024 and not to_update:
            message(log_file, 'EXISTS', directory, '%d image(s) => %s' % (len(files), output_ebook))
        else:
            try:
                new_files = set()
                for file in files:
                    if convert_images:
                        new_files.add(self.convert_image(log_file, file))
                    else:
                        new_files.add(file)
                output_directory.mkdir()
                with zipfile.ZipFile(
                        output_ebook.path, mode='w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as ebook:
                    for file in sorted(new_files):
                        ebook.write(file.path, file.get_basename())
            except Exception as e:
                fatal_error(log_file, directory, '%d image(s) => %s: %s' % (len(files), output_ebook, e))
            else:
                message(log_file, 'SUCCESS', directory, '%d image(s) => %s%s' % (len(files), output_ebook, ' (updated)' if to_update else ''))

    def visit(self, directory: AbsolutePath, log_file):
        assert directory.isdir()
        folders = []
        files = []
        for path_name in directory.listdir():
            path = AbsolutePath.join(directory, path_name)
            # Ignore gif files.
            if path.isfile() and path.extension != 'gif':
                files.append(path)
            elif path.isdir():
                folders.append(path)
        if folders and files:
            extensions = {file.extension for file in files}
            if any(extension in SUPPORTED_EXTENSIONS for extension in extensions):
                # Found images.
                for file in files:
                    if file.title != directory.title and REGEX_NUMBER.search(file.title):
                        return fatal_error(
                            log_file,
                            directory,
                            'Found folders and an image with number in name: %s' % file.get_basename())
                # Images found are not considered as ebook content. They can be ignored.
            # Either not images found, or found files considered as irrelevant.
            # Files can be ignored, to fall in case `folders and not files`.
            files.clear()
        if not folders and not files:
            return message(log_file, 'PASSED', directory, 'empty')
        if not folders and files:
            extensions = {file.extension for file in files}
            if extensions and all(extension in SUPPORTED_EXTENSIONS for extension in extensions):
                # Found a folder with only files that all belong to supported extension.
                # This folder must be compressed.
                self.convert_to_ebook(directory, files, log_file)
            else:
                return message(log_file, 'PASSED', directory, 'no supported extension: %s' % extensions)
        if folders and not files:
            for folder in folders:
                self.visit(folder, log_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', help='folder input')
    parser.add_argument('--output', '-o', help='folder output')
    parser.add_argument('--log', '-l', default=None, help='log file')
    args = parser.parse_args()
    Converter(args)


if __name__ == '__main__':
    main()
