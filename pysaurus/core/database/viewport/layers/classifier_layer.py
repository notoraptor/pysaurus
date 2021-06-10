from typing import Iterable, List

from pysaurus.core import functions
from pysaurus.core.database.video import Video
from pysaurus.core.database.viewport.layers.grouping_layer import GroupingLayer
from pysaurus.core.database.viewport.layers.layer import Layer
from pysaurus.core.database.viewport.viewtools.group import Group
from pysaurus.core.database.viewport.viewtools.group_array import GroupArray
from pysaurus.core.database.viewport.viewtools.group_def import GroupDef


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

    def classify_videos(
        self, videos: Iterable[Video], prop_name: str, values: List
    ) -> GroupArray:
        classes = {}
        for video in videos:
            for value in video.properties.get(prop_name, []):
                classes.setdefault(value, []).append(video)
        if values:
            latest_value = values[-1]
            for value in values[:-1]:
                classes.pop(value)
            latest_group = Group(None, classes.pop(latest_value))
            other_groups = [
                Group(field_value, group_videos)
                for field_value, group_videos in classes.items()
            ]
            groups = (
                other_groups if latest_group is None else [latest_group] + other_groups
            )
        else:
            groups = [
                Group(field_value, group_videos)
                for field_value, group_videos in classes.items()
            ]
        field = ":" + prop_name
        if self.parent and isinstance(self.parent, GroupingLayer):
            return GroupArray(field, self.parent.get_grouping().sort(groups))
        else:
            return GroupArray(field, GroupDef.sort_groups(groups, field))

    def filter(self, data: GroupArray) -> GroupArray:
        if data.field is None or data.field[0] != ":":
            return data
        prop_name = data.field[1:]
        if not self.database.get_prop_type(prop_name).multiple:
            return data
        path = self.get_path()
        if not path:
            return data
        videos = set(data.lookup(path[0]).videos)
        for value in path[1:]:
            videos &= set(data.lookup(value).videos)
        assert videos
        return self.classify_videos(videos, prop_name, path)

    def remove_from_cache(self, cache: GroupArray, video: Video):
        groups = []
        if len(cache) == 1 and cache[0].field_value is None:
            groups.append(cache[0])
        else:
            field_name = cache.field
            if field_name[0] == ":":
                prop_type = self.database.get_prop_type(field_name[1:])
                if prop_type.multiple:
                    field_value = video.properties.get(field_name[1:], [None])
                else:
                    field_value = [
                        video.properties.get(field_name[1:], prop_type.default)
                    ]
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
        field = self._cache.field
        if field and field[0] == ":":
            converter = functions.identity
        else:
            converter = str
        return [
            {"value": converter(g.field_value), "count": len(g.videos)}
            for g in self._cache
        ]
