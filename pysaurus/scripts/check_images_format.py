import sys
from pysaurus.core.components import AbsolutePath
from PIL import Image
from typing import Dict, List
import os


def main():
    if len(sys.argv) != 2:
        raise RuntimeError("No folder specified")
    folder = AbsolutePath(sys.argv[1])
    if not folder.isdir():
        raise RuntimeError(f"Not a folder: {folder}")
    nb_skipped = 0
    nb_files = 0
    format_to_images = {}  # type: Dict[str, List[AbsolutePath]]
    for i, name in enumerate(folder.listdir()):
        path = AbsolutePath.join(folder, name)
        if path.isfile():
            try:
                img = Image.open(path.path)
            except Exception:
                print('Skipped', path)
                nb_skipped += 1
            else:
                nb_files += 1
                format_to_images.setdefault(img.format, []).append(path)
                del img
        if (i + 1) % 100 == 0:
            print('Parsed', i + 1)
    if len(format_to_images) == 1:
        return
    print('Skipped', nb_skipped, 'file(s)')
    print('Checked', nb_files, 'file(s) with', len(format_to_images), 'format(s)')
    for format, images in format_to_images.items():
        new_folder = AbsolutePath.join(folder, format)
        if not new_folder.exists():
            new_folder.mkdir()
        if not new_folder.isdir():
            raise RuntimeError(f"Cannot locate or create a folder for format {format} in {folder}")
        print('Moving', len(images), 'image(s) to', new_folder)
        for i, old_path in enumerate(images):
            new_path = AbsolutePath.join(new_folder, old_path.get_basename())
            os.rename(old_path.path, new_path.path)
            assert not old_path.exists()
            assert new_path.isfile()
            if (i + 1) % 100 == 0:
                print('Moved', i + 1)


if __name__ == '__main__':
    main()
