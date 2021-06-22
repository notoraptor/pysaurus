from typing import List

from pysaurus.core.miniature import Miniature
from .group_computer import GroupComputer
from .pixel_group import PixelGroup


class CornerGroupComputer(GroupComputer):
    def compute_groups(self, miniature: Miniature) -> List[PixelGroup]:
        corner_zones = miniature.get_corner_zones()
        groups_tl = self.group_pixels(corner_zones.tl, corner_zones.w, corner_zones.h)
        groups_tr = self.group_pixels(corner_zones.tr, corner_zones.w, corner_zones.h)
        groups_bl = self.group_pixels(corner_zones.bl, corner_zones.w, corner_zones.h)
        groups_br = self.group_pixels(corner_zones.br, corner_zones.w, corner_zones.h)
        groups_tl.sort(key=lambda g: len(g.members), reverse=True)
        groups_tr.sort(key=lambda g: len(g.members), reverse=True)
        groups_bl.sort(key=lambda g: len(g.members), reverse=True)
        groups_tr.sort(key=lambda g: len(g.members), reverse=True)
        return [groups_tl[0], groups_tr[0], groups_bl[0], groups_br[0]]
