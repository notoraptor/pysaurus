import sys
from collections import Counter

from pysaurus.core.components import AbsolutePath


def main():
    if len(sys.argv) != 2:
        print("No path specified.")
        return
    folder = AbsolutePath(sys.argv[1]).assert_dir()
    lines = Counter()
    for file_name in folder.listdir():
        path = AbsolutePath.join(folder, file_name)
        if path.isfile():
            with open(path.path) as file:
                for line in file:
                    lines.update([line.strip()])
    inv = {}
    for line, count in lines.items():
        inv.setdefault(count, []).append(line)
    for count in sorted(inv, reverse=True):
        for line in sorted(inv[count]):
            print(f"{count}\t{line}")


if __name__ == "__main__":
    main()
