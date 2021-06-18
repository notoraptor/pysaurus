import math
import os
import sys

from pysaurus.core.components import AbsolutePath
from pysaurus.core.profiling import Profiler


def main():
    if len(sys.argv) != 3:
        raise RuntimeError("Required folder and chunk size")
    folder = AbsolutePath(sys.argv[1])
    chunk_size = int(sys.argv[2])
    if not folder.isdir():
        raise RuntimeError(f"Not a folder: {folder}")
    if chunk_size < 2:
        raise RuntimeError(f"Useless to split a folder per {chunk_size} files")
    with Profiler("Collect paths"):
        paths = [AbsolutePath.join(folder, name) for name in folder.listdir()]
    nb_chunks = (len(paths) // chunk_size) + bool(len(paths) % chunk_size)
    print("Expected", nb_chunks, "sub-folders")
    chunks = []
    for i in range(nb_chunks):
        start = i * chunk_size
        limit = start + chunk_size
        chunks.append(paths[start:limit])
    assert sum(len(chunk) for chunk in chunks) == len(paths)
    len_str_chunk_id = int(math.log10(len(chunks))) + 1
    for chunk_id, chunk in enumerate(chunks):
        new_folder = AbsolutePath.join(
            folder, f"{folder.title}-{str(chunk_id).rjust(len_str_chunk_id, '0')}"
        )
        if not new_folder.exists():
            new_folder.mkdir()
        if not new_folder.isdir():
            raise RuntimeError(f"Cannot found or create new folder {new_folder}")
        print("Moving files to", new_folder.title)
        for i, old_path in enumerate(chunk):
            new_path = AbsolutePath.join(new_folder, old_path.get_basename())
            os.rename(old_path.path, new_path.path)
            assert not old_path.exists()
            assert new_path.exists()
            if (i + 1) % 100 == 0:
                print(f"\tMoved {i + 1}")


if __name__ == "__main__":
    main()
