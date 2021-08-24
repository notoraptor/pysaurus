from typing import Sequence

from pysaurus.database.video import Video
from pysaurus.database.viewport.layers.layer import Layer
from pysaurus.database.viewport.viewtools.group import Group


class GroupLayer(Layer):
    __slots__ = ()
    __props__ = ("group_id",)

    _cache: Group

    def set_group_id(self, group_id: int):
        self._set_parameters(group_id=max(group_id, 0))

    def get_group_id(self) -> int:
        return self.get_parameter("group_id")

    def _clip_group_id(self, nb_groups):
        self.set_group_id(min(self.get_group_id(), nb_groups - 1))
        return self.get_group_id()

    def reset_parameters(self):
        self.set_group_id(0)

    def filter(self, data: Sequence[Group]) -> Group:
        return data[self._clip_group_id(len(data))] if data else Group()

    def remove_from_cache(self, cache: Group, video: Video):
        if video in cache.videos:
            cache.videos.remove(video)
        if not cache.videos:
            self.request_update()
