from typing import List, Set

from pysaurus.core import functions
from pysaurus.database.video import Video
from pysaurus.database.viewport.layers.grouping_layer import GroupingLayer
from pysaurus.database.viewport.layers.layer import Layer
from pysaurus.database.viewport.viewtools.group import Group
from pysaurus.database.viewport.viewtools.group_array import GroupArray


class ClassifierLayer(Layer):
    __slots__ = ()
    __props__ = ("path",)
    _cache: GroupArray

    def set_path(self, path: list):
        self._set_parameters(path=path)

    def get_path(self) -> list:
        return self.get_parameter("path")

    def reset_parameters(self):
        self._set_parameters(path=[])

    def filter(self, data: GroupArray) -> GroupArray:
        if data.field is None or not data.is_property:
            return data
        if not self.database.get_prop_type(data.field).multiple:
            return data
        path = self.get_path()
        if not path:
            return data
        videos = set(data.lookup(path[0]).videos)
        for value in path[1:]:
            videos &= set(data.lookup(value).videos)
        assert videos, path
        return self._classify_videos(videos, data.field, path)

    def _classify_videos(
        self, videos: Set[Video], prop_name: str, values: List
    ) -> GroupArray:
        assert values
        assert self.parent and isinstance(self.parent, GroupingLayer)
        classes = {}
        for video in videos:
            for value in video.properties.get(prop_name, []):
                classes.setdefault(value, []).append(video)
        for value in values:
            classes.pop(value)
        groups = [Group(None, videos)] + [
            Group(field_value, group_videos)
            for field_value, group_videos in classes.items()
        ]
        return GroupArray(prop_name, True, self.parent.get_grouping().sort(groups))

    def remove_from_cache(self, cache: GroupArray, video: Video):
        groups = []
        if len(cache) == 1 and cache[0].field_value is None:
            groups.append(cache[0])
        else:
            if cache.is_property:
                prop_type = self.database.get_prop_type(cache.field)
                if prop_type.multiple:
                    field_value = video.properties.get(cache.field, None) or [None]
                else:
                    field_value = [video.properties.get(cache.field, prop_type.default)]
            else:
                field_value = [getattr(video, cache.field)]
            for value in field_value:
                if cache.contains_key(value):
                    groups.append(cache.lookup(value))
        for group in groups:
            if video in group.videos:
                group.videos.remove(video)
                if not group.videos:
                    group.videos.clear()
                    cache.remove(group)

    def get_group_value(self, index):
        return self._cache[index].field_value

    def get_group_id(self, value):
        return self._cache.lookup_index(value)

    def get_stats(self):
        if self._cache.field and self._cache.is_property:
            converter = functions.identity
        else:
            converter = str
        return [
            {"value": converter(g.field_value), "count": len(g.videos)}
            for g in self._cache
        ]
