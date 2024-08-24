from typing import List, Sequence

from pysaurus.video.video_constants import VIDEO_FLAGS


def parse_sources(paths: Sequence[Sequence[str]]) -> List[List[str]]:
    if not paths:
        sources = [["readable"]]
    else:
        valid_paths = set()
        for path in paths:
            path = tuple(path)
            if path not in valid_paths:
                assert len(set(path)) == len(path)
                assert all(flag in VIDEO_FLAGS for flag in path)
                valid_paths.add(path)
        sources = [list(path) for path in sorted(valid_paths)]
    return sources


def parse_sorting(sorting: Sequence[str]) -> List[str]:
    return list(sorting) if sorting else ["-date"]
