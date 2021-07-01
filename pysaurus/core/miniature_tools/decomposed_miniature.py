from typing import Any, List

from pysaurus.core.miniature_tools.pixel_group import PixelGroup


class DecomposedMiniature:
    __slots__ = ("miniature_identifier", "pixel_groups")
    miniature_identifier: Any
    pixel_groups: List[PixelGroup]

    def __init__(self, miniature_identifier, pixel_groups):
        self.miniature_identifier = miniature_identifier
        self.pixel_groups = pixel_groups
