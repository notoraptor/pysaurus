import argparse

import ujson as json

from pysaurus.core import functions
from pysaurus.core.components import AbsolutePath
from pysaurus.core.constants import CPU_COUNT
from pysaurus.core.profiling import Profiler


def job_get_sizes(job):
    filenames, job_id, folder = job
    size_to_files = {}
    for i, filename in enumerate(filenames):
        file_path = AbsolutePath.join(folder, filename)
        if file_path.isfile():
            size = file_path.get_size()
            size_to_files.setdefault(size, []).append(file_path)
        if (i + 1) % 100 == 0:
            print(f"[Job {job_id}] parsed {i + 1}/{len(filenames)}")
    return size_to_files


def _p(folder, filenames):
    size_to_files = {}
    jobs = functions.dispatch_tasks(filenames, CPU_COUNT, [folder])
    tables = functions.parallelize(job_get_sizes, jobs, CPU_COUNT)
    for sizes in tables:
        for size, files in sizes.items():
            size_to_files.setdefault(size, []).extend(files)
    return size_to_files


def _f(folder, filenames):
    size_to_files = {}
    for i, filename in enumerate(filenames):
        file_path = AbsolutePath.join(folder, filename)
        if file_path.isfile():
            size = file_path.get_size()
            size_to_files.setdefault(size, []).append(file_path)
        if (i + 1) % 2000 == 0:
            print("Parsed", i + 1, "file(s)")
    return size_to_files


def main():
    parser = argparse.ArgumentParser(description="Find duplicate files in a folder.")
    parser.add_argument(
        "-d", "--directory", required=True, help="Folder to find files (not recursive)"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Name of JSON file to save output"
    )
    args = parser.parse_args()
    folder = AbsolutePath(args.directory)
    if not folder.isdir():
        print("Expected a directory, got", folder)
        exit(-1)
    print("Folder:", folder)
    print("Get filenames")
    filenames = list(folder.listdir())
    print("Found", len(filenames), "filename(s)")
    with Profiler("Group by size"):
        size_to_files = _f(folder, filenames)
    print("Getting duplicates")
    duplicates = {
        size: files for size, files in size_to_files.items() if len(files) > 1
    }
    print("Found", len(duplicates), "duplicate(s)")
    print("Save results")
    output = [
        [size, [str(f) for f in files]] for size, files in sorted(duplicates.items())
    ]
    with open(args.output, "w") as file:
        json.dump(output, file)
    print("Saved")


if __name__ == "__main__":
    main()
