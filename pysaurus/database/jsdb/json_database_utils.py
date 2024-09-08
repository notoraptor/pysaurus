import logging
import sys
from collections import namedtuple
from typing import Callable, List, Union

from pysaurus.core.constants import PYTHON_ERROR_THUMBNAIL

logger = logging.getLogger(__name__)

DatabaseChanges = namedtuple("DatabaseChanges", ("removed", "replaced", "modified"))


def _patch_version_0(data: dict, version) -> bool:
    if version >= 0:
        return False
    assert version == -1
    # Update video property values.
    # Convert any non-list value to sorted list.
    for video_dict in data.get("videos", ()):  # type: dict
        for name in list(video_dict.get("p", ())):
            values = video_dict["p"][name]
            if values is not None:
                if not isinstance(values, list):
                    values = [values]
                elif not values:
                    values = None
                else:
                    values = sorted(values)
            if values is None:
                del video_dict["p"][name]
            else:
                video_dict["p"][name] = values
    return True


def _patch_version_1(data: dict, version) -> bool:
    if version >= 1:
        return False
    # Remove video["R"]["t"] (video.runtime.has_thumbnail)
    for video_dict in data.get("videos", ()):  # type: dict
        if "R" in video_dict:
            video_dict["R"].pop("t", None)
    return True


def _patch_version_2(data: dict, version) -> bool:
    if version >= 2:
        return False
    # Remove PYTHON_ERROR_THUMBNAIL error
    for video_dict in data.get("videos", ()):  # type: dict
        if PYTHON_ERROR_THUMBNAIL in video_dict.get("e", ()):
            errors = sorted(set(video_dict["e"]) - {PYTHON_ERROR_THUMBNAIL})
            video_dict["e"] = errors
            print("-PYTHON_ERROR_THUMBNAILS", video_dict["f"], file=sys.stderr)
    return True


_PATCHS: List[Callable[[Union[dict, list], int], bool]] = [
    _patch_version_0,
    _patch_version_1,
    _patch_version_2,
]


def patch_database_json(data: Union[dict, list], version):
    for patch in _PATCHS:
        print(patch.__name__)
        if patch(data, version):
            return
    raise RuntimeError(f"No patch found for version {version}")
