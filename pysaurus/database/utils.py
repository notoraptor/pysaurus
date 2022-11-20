import os
import tempfile

TEMP_DIR = tempfile.gettempdir()
TEMP_PREFIX = tempfile.gettempprefix() + "_pysaurus_"

DEFAULT_SOURCE_DEF = [("readable",)]


def generate_temp_file_path(extension) -> str:
    temp_file_id = 0
    while True:
        temp_file_path = os.path.join(
            TEMP_DIR, f"{TEMP_PREFIX}{temp_file_id}.{extension}"
        )
        try:
            with open(temp_file_path, "x"):
                return temp_file_path
        except FileExistsError:
            temp_file_id += 1
