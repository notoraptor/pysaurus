import os

import ujson as json

from pysaurus.core.components import AbsolutePath
from pysaurus.core.modules import FileSystem
from pysaurus.core.profiling import Profiler


def main():
    folder = AbsolutePath("my_folder")
    if folder.exists():
        assert folder.isdir()
        folder.delete()
    folder.mkdir()
    nb_keys = 30
    nb_files = 30_000
    model = {f"{i+1}": "_" * 10 for i in range(nb_keys)}
    with Profiler("write"):  # 10 seconds
        for i in range(nb_files):
            with open(os.path.join(folder.path, f"{i+1}.json"), "w") as file:
                json.dump(model, file)
    with Profiler("read"):  # 4 seconds
        l = []
        for path in FileSystem.scandir(folder.path):
            with open(path.path) as file:
                l.append(json.load(file))
    assert len(l) == nb_files


if __name__ == "__main__":
    main()
