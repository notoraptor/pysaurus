from typing import Optional, Dict

from pysaurus.core.components import AbsolutePath
from pysaurus.core.database.video import Video
from pysaurus.core.database.viewport.layers.layer import Layer
from pysaurus.core.database.viewport.viewtools.group import Group
from pysaurus.core.database.viewport.viewtools.group_array import GroupArray
from pysaurus.core.database.viewport.viewtools.group_def import GroupDef


class GroupingLayer(Layer):
    __slots__ = ()
    __props__ = ("grouping",)
    _cache: GroupArray
    DEFAULT_GROUP_DEF = GroupDef.none()  # str field, bool reverse

    def set_grouping(
        self,
        *,
        field: Optional[str] = None,
        sorting: Optional[str] = None,
        reverse: Optional[bool] = None,
        allow_singletons: Optional[bool] = None,
        allow_multiple: Optional[bool] = None
    ):
        self._set_parameters(
            grouping=self.get_grouping().copy(
                field, sorting, reverse, allow_singletons, allow_multiple
            )
        )

    def get_grouping(self) -> GroupDef:
        return self.get_parameter("grouping")

    def reset_parameters(self):
        self._set_parameters(grouping=self.DEFAULT_GROUP_DEF)

    def filter(self, data: Dict[AbsolutePath, Video]) -> GroupArray:
        group_def = self.get_grouping()
        groups = []
        if not group_def:
            groups.append(Group(None, list(data.values())))
        elif group_def.allow_singletons or group_def.allow_multiple:
            grouped_videos = {}
            if group_def.field[0] == ":":
                field = group_def.field[1:]
                prop_type = self.database.get_prop_type(field)
                if prop_type.multiple:
                    for video in data.values():
                        values = video.properties.get(field, None) or [None]
                        for value in values:
                            grouped_videos.setdefault(value, []).append(video)
                else:
                    for video in data.values():
                        grouped_videos.setdefault(
                            video.properties.get(field, prop_type.default), []
                        ).append(video)
            else:
                for video in data.values():
                    grouped_videos.setdefault(
                        getattr(video, group_def.field), []
                    ).append(video)
            for field_value, videos in grouped_videos.items():
                if (
                    field_value is None
                    or (group_def.allow_singletons and len(videos) == 1)
                    or (group_def.allow_multiple and len(videos) > 1)
                ):
                    groups.append(Group(field_value, videos))
            groups = group_def.sort(groups)
        return GroupArray(group_def.field, groups)

    def remove_from_cache(self, cache: GroupArray, video: Video):
        groups = []
        if len(cache) == 1 and cache[0].field_value is None:
            groups.append(cache[0])
        else:
            field_name = self.get_grouping().field
            if field_name[0] == ":":
                prop_type = self.database.get_prop_type(field_name[1:])
                if prop_type.multiple:
                    field_value = video.properties.get(field_name[1:], [None])
                else:
                    field_value = [
                        video.properties.get(field_name[1:], prop_type.default)
                    ]
            else:
                field_value = [getattr(video, self.get_grouping().field)]
            for value in field_value:
                if cache.contains_key(value):
                    groups.append(cache.lookup(value))
        for group in groups:
            if video in group.videos:
                group.videos.remove(video)
                if not group.videos or (
                    not self.get_grouping().allow_singletons and len(group.videos) == 1
                ):
                    group.videos.clear()
                    cache.remove(group)

    def get_group_id(self, value):
        return self._cache.lookup_index(value)
