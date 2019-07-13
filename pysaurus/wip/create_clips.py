import sys

from pysaurus.core import video_clipping
from pysaurus.core.components.absolute_path import AbsolutePath


def main():
    if len(sys.argv) != 2:
        return
    file_name = sys.argv[1]
    file_path = AbsolutePath(file_name)
    duration = video_clipping.video_duration(file_path.path)
    cursor = 0
    clip_seconds = 10
    unique_id = str(AbsolutePath.join(file_path.get_directory(), file_path.title))
    while cursor < duration:
        video_clipping.video_clip(file_path.path, cursor, clip_seconds, unique_id)
        cursor += clip_seconds


if __name__ == '__main__':
    main()
