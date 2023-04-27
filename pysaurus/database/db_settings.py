from pysaurus.core.json_type import Type
from pysaurus.core.schematizable import Schema, WithSchema, schema_prop


class DbSettings(WithSchema):
    __slots__ = ()
    SCHEMA = Schema(
        (
            Type("miniature_pixel_distance_radius", int, 6),
            Type("miniature_group_min_size", int, 0),
        )
    )

    miniature_pixel_distance_radius = schema_prop("miniature_pixel_distance_radius")
    miniature_group_min_size = schema_prop("miniature_group_min_size")
