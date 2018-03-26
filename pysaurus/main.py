import sys

from pysaurus.database import Databases
from pysaurus.utils.absolute_path import AbsolutePath

if len(sys.argv) == 2:
    list_file_path = AbsolutePath(sys.argv[1])
    if not (list_file_path.exists() and list_file_path.isfile()):
        print("Expected a valid file name as argument.")
        exit(1)
    database_folder_path = AbsolutePath.join(list_file_path.get_dirname(), list_file_path.title)
    folder_paths = []
    with open(list_file_path.path, 'r') as list_file:
        for line in list_file:
            line = line.strip()
            if line and not line.startswith('#'):
                folder_path = AbsolutePath(line)
                if folder_path.exists() and folder_path.isdir():
                    folder_paths.append(folder_path)
                else:
                    print('Ignored', folder_path)
    database = Databases.get(database_folder_path, folder_paths, reset_paths=True)
    database.save()
