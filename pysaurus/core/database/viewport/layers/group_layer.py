from typing import Sequence

from pysaurus.core.database.video import Video
from pysaurus.core.database.viewport.viewtools.group import Group
from pysaurus.core.database.viewport.layers.layer import Layer


class GroupLayer(Layer):
    __slots__ = ()
    __props__ = ("group_id",)

    _cache: Group

    def set_group_id(self, group_id: int):
        if group_id < 0:
            group_id = 0
        self._set_parameters(group_id=group_id)

    def get_group_id(self) -> int:
        return self.get_parameter("group_id")

    def _clip_group_id(self, nb_groups):
        group_id = self.get_group_id()
        if group_id >= nb_groups:
            group_id = nb_groups - 1
            self.set_group_id(group_id)
        return self.get_group_id()

    def reset_parameters(self):
        self.set_group_id(0)

    def filter(self, data: Sequence[Group]) -> Group:
        return data[self._clip_group_id(len(data))]

    def remove_from_cache(self, cache: Group, video: Video):
        if video in cache.videos:
            cache.videos.remove(video)
        if not cache.videos:
            self.request_update()

    def get_field_value(self):
        return self._cache.field_value
