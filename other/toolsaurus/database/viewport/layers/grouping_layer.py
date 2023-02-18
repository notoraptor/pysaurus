from typing import Dict, Optional

from other.toolsaurus.database.viewport.layers.layer import Layer
from pysaurus.core.components import AbsolutePath
from pysaurus.database.viewport.view_tools import Group, GroupArray, GroupDef
from pysaurus.video.video import Video


class GroupingLayer(Layer):
    __slots__ = ()
    __props__ = ("grouping",)
    _cache: GroupArray
    DEFAULT_GROUP_DEF = GroupDef()  # str field, bool reverse

    def set_grouping(
        self,
        *,
        field: Optional[str] = None,
        is_property: Optional[bool] = None,
        sorting: Optional[str] = None,
        reverse: Optional[bool] = None,
        allow_singletons: Optional[bool] = None,
    ):
        self._set_parameters(
            grouping=self.get_grouping().copy(
                field, is_property, sorting, reverse, allow_singletons
            )
        )

    def get_grouping(self) -> GroupDef:
        return self._get_parameter("grouping")

    def reset_parameters(self):
        self._set_parameters(grouping=self.DEFAULT_GROUP_DEF)

    def _get_prop_vals(self, name, video_state):
        return self.database.get_prop_values(video_state, name, default=True) or [None]

    def _filter(self, data: Dict[AbsolutePath, Video]) -> GroupArray:
        group_def = self.get_grouping()
        groups = []
        if not group_def:
            groups.append(Group(None, list(data.values())))
        else:
            grouped_videos = {}
            if group_def.is_property:
                for video in data.values():
                    for value in self._get_prop_vals(group_def.field, video):
                        grouped_videos.setdefault(value, []).append(video)
            else:
                for video in data.values():
                    grouped_videos.setdefault(
                        getattr(video, group_def.field, None), []
                    ).append(video)
                # hack
                if group_def.field == "similarity_id":
                    # Remove None (not checked) and -1 (not similar) videos.
                    grouped_videos.pop(None, None)
                    grouped_videos.pop(-1, None)
            for field_value, videos in grouped_videos.items():
                if group_def.allow_singletons or len(videos) > 1:
                    groups.append(Group(field_value, videos))
            groups = group_def.sort(groups)
        return GroupArray(group_def.field, group_def.is_property, groups)

    def _remove_from_cache(self, cache: GroupArray, video: Video):
        groups = []
        if len(cache) == 1 and cache[0].field_value is None:
            groups.append(cache[0])
        else:
            group_def = self.get_grouping()
            if group_def.is_property:
                field_value = self._get_prop_vals(group_def.field, video)
            else:
                field_value = [getattr(video, group_def.field, None)]
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
