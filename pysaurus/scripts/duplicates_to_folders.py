import argparse
import hashlib
import math
import os

import ujson as json

from pysaurus.core.components import AbsolutePath, FileSize, FilePath
from pysaurus.core.profiling import Profiler


def hash_file(file_path: AbsolutePath):
    hasher = hashlib.blake2b()
    with open(file_path.path, "rb") as file:
        content = file.read()
        hasher.update(content)
    return hasher.hexdigest()


def main():
    parser = argparse.ArgumentParser(
        description="Move duplicates into separate folders"
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input JSON file listing duplicates, generated by `find_duplicate_files`",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output folder to generate duplicate sub-folders.",
    )
    args = parser.parse_args()

    output_folder = AbsolutePath(args.output)
    if not output_folder.exists():
        print("Create output folder", output_folder)
        output_folder.mkdir()
    if not output_folder.isdir():
        print("No folder found at output path", output_folder)
        exit(-1)

    with open(args.input) as file:
        duplicates = json.load(file)
    duplicates = [
        [size, [AbsolutePath(f) for f in files]] for size, files in duplicates
    ]
    print("Loaded", len(duplicates), "duplicate(s)")
    with Profiler("Consolidate duplicates"):
        filtered_duplicates = []
        for i, (size, files) in enumerate(duplicates):
            filtered_files = [f for f in files if f.exists()]
            if len(filtered_files) < 2:
                continue
            hash_to_files = {}
            for path in filtered_files:
                hash_to_files.setdefault(hash_file(path), []).append(path)
            filtered_duplicates.extend(
                [size, fs] for fs in hash_to_files.values() if len(fs) > 1
            )
            if (i + 1) % 100 == 0:
                print(
                    "Consolidated", i + 1, "currently found", len(filtered_duplicates)
                )
        duplicates = filtered_duplicates

    duplicates.sort()
    nb_files = 0
    total_size = 0
    max_size = 0
    for size, files in duplicates:
        nb_files += len(files)
        total_size += size * len(files)
        max_size = max(max_size, size)
    print(
        "Loaded",
        len(duplicates),
        "duplicate(s) for",
        nb_files,
        "file(s) with total size",
        FileSize(total_size),
        "from",
        duplicates[0][0],
        "to",
        duplicates[-1][0],
    )
    len_size_string = int(math.log10(max_size)) + 1
    movements = []
    folders = []
    with Profiler("Generate move args"):
        for i, (size, files) in enumerate(duplicates):
            dup_folder_path = AbsolutePath.join(
                output_folder, str(size).rjust(len_size_string, "0")
            )
            folders.append(dup_folder_path)
            len_title_writing = int(math.log10(len(files))) + 1
            for file_no, file_path in enumerate(files):
                output_file_path = FilePath(
                    dup_folder_path,
                    file_path.title,
                    file_path.extension,
                )
                movements.append((file_path, output_file_path))
            if (i + 1) % 100 == 0:
                print("Handled", i + 1, "duplicate(s)")
    with Profiler("Create duplicate folders"):
        for folder in folders:
            if not folder.exists():
                folder.mkdir()
            if not folder.isdir():
                raise RuntimeError(f"Unable to create or locate folder {folder}")
    with Profiler("Move duplicate files"):
        for i, (inp, out) in enumerate(movements):
            os.rename(inp.path, out.path)
            assert not inp.exists()
            assert out.isfile()
            if (i + 1) % 100 == 0:
                print("Moved", i + 1)


if __name__ == "__main__":
    main()