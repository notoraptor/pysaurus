from typing import Dict

from other.legacy.pysaurus.miniature.group_computer import GroupComputer
from pysaurus.core.informer import Informer
from pysaurus.core.json_type import Type
from pysaurus.core.schematizable import Schema, WithSchema, schema_prop
from pysaurus.database.algorithms.miniatures import Miniatures
from pysaurus.miniature.miniature import Miniature


class GroupSignature(WithSchema):
    __slots__ = ()
    SCHEMA = Schema((Type("r", int), Type("m", int), Type("n", int)))
    r = schema_prop("r")  # pixel_distance_radius
    m = schema_prop("m")  # group_min_size
    n = schema_prop("n")  # nb_groups


class LegacyMiniature(Miniature):
    __slots__ = ("group_signature",)

    def __init__(
        self, red, green, blue, width, height, identifier=None, group_signature=None
    ):
        super().__init__(red, green, blue, width, height, identifier)
        self.group_signature = group_signature

    def set_group_signature(
        self, pixel_distance_radius, group_min_size: int, nb_groups: int
    ):
        self.group_signature = GroupSignature.from_keys(
            r=pixel_distance_radius, m=group_min_size, n=nb_groups
        )

    def has_group_signature(self, pixel_distance_radius: int, group_min_size: int):
        return (
            self.group_signature
            and self.group_signature.r == pixel_distance_radius
            and self.group_signature.m == group_min_size
        )


class LegacyMiniatures(Miniatures):
    @classmethod
    def update_group_signatures(
        cls,
        miniatures: Dict[str, LegacyMiniature],
        pixel_distance_radius,
        group_min_size,
    ):
        m_no_groups = [
            m
            for m in miniatures.values()
            if not m.has_group_signature(pixel_distance_radius, group_min_size)
        ]
        if m_no_groups:
            group_computer = GroupComputer(
                group_min_size=group_min_size,
                pixel_distance_radius=pixel_distance_radius,
            )
            for dm in group_computer.batch_compute_groups(
                m_no_groups, notifier=Informer.default()
            ):
                miniatures[dm.miniature_identifier].set_group_signature(
                    pixel_distance_radius, group_min_size, len(dm.pixel_groups)
                )
