from pysaurus.core.jsonable import Jsonable


class DbSettings(Jsonable):
    miniature_pixel_distance_radius: int = 6
    miniature_group_min_size: int = 0
