import os
import shutil
import sys
from datetime import datetime
from time import gmtime, strftime


def main():
    if len(sys.argv) != 3:
        print("Expected arguments: <archivename> <foldertocompress>")
        exit(1)
    archive_name, folder = sys.argv[1:]
    if not os.path.isdir(folder):
        print("Cannot find folder to compress:", folder)
        exit(1)
    current_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    time_zone = strftime("%z", gmtime())
    base_name = f"{archive_name}-{current_time}{time_zone}"
    print("Compressing into", f"{base_name}.zip")
    shutil.make_archive(base_name, "zip", folder)


if __name__ == "__main__":
    main()
