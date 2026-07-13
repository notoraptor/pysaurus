from typing import Sequence

from pysaurus.core.constants import VIDEO_DEFAULT_SORTING
from pysaurus.video.video_constants import VIDEO_FLAGS
from pysaurus.video.video_sorting import VideoSorting


def parse_sources(paths: Sequence[Sequence[str]]) -> list[list[str]]:
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


def parse_sorting(sorting: Sequence[str]) -> list[str]:
    # Empty means "use the default order": this is a view-layer policy, kept out
    # of the pure VideoSorting model. Otherwise delegate to VideoSorting, the
    # single authority that parses and deduplicates a sort spec; to_string_list()
    # returns the canonical form (explicit +/- signs, duplicates dropped).
    if not sorting:
        return list(VIDEO_DEFAULT_SORTING)
    return VideoSorting(sorting).to_string_list()
