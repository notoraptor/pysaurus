from typing import List

from pysaurus.core.miniature_tools.group_computer import GroupComputer
from pysaurus.core.miniature_tools.miniature import Miniature
from pysaurus.core.miniature_tools.pixel_group import PixelGroup
from pysaurus.other.tests.image_management.elements import miniature_utils


class CornerGroupComputer(GroupComputer):
    def compute_groups(self, miniature: Miniature) -> List[PixelGroup]:
        corner_zones = miniature_utils.get_corner_zones(miniature)
        groups_tl = self.group_pixels(corner_zones.tl)
        groups_tr = self.group_pixels(corner_zones.tr)
        groups_bl = self.group_pixels(corner_zones.bl)
        groups_br = self.group_pixels(corner_zones.br)
        groups_tl.sort(key=lambda g: len(g.members), reverse=True)
        groups_tr.sort(key=lambda g: len(g.members), reverse=True)
        groups_bl.sort(key=lambda g: len(g.members), reverse=True)
        groups_tr.sort(key=lambda g: len(g.members), reverse=True)
        return [groups_tl[0], groups_tr[0], groups_bl[0], groups_br[0]]
