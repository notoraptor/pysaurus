from typing import Any, List, Sequence

from pysaurus.database.viewport.abstract_video_provider import AbstractVideoProvider
from pysaurus.database.viewport.view_tools import GroupDef, LookupArray, SearchDef
from pysaurus.video.video_utils import VIDEO_FLAGS


def parse_sources(paths: Sequence[Sequence[str]]) -> List[List[str]]:
    if not paths:
        sources = [["readable"]]
    else:
        valid_paths = set()
        for path in paths:
            path = tuple(path)
            if path not in valid_paths:
                assert len(set(path)) == len(path)
                assert all(flag in VIDEO_FLAGS for flag in path)
                valid_paths.add(path)
        sources = [list(path) for path in sorted(valid_paths)]
    return sources


def parse_grouping(
    field, is_property=None, sorting=None, reverse=None, allow_singletons=None
) -> GroupDef:
    return GroupDef(field, is_property, sorting, reverse, allow_singletons)


def parse_sorting(sorting: Sequence[str]) -> List[str]:
    return list(sorting) or ["-date"]


class GroupCount:
    __slots__ = ("value", "count")

    def __init__(self, value, count):
        self.value = value
        self.count = count

    @classmethod
    def keyof(cls, group_count):
        # type: (GroupCount) -> Any
        return group_count.value


class SaurusProvider(AbstractVideoProvider):
    __slots__ = (
        "sources",
        "grouping",
        "classifier",
        "group",
        "search",
        "sorting",
        "_groups",
        "_view_indices",
        "_to_update",
    )

    def __init__(self, database):
        super().__init__(database)
        self.sources: List[List[str]] = []
        self.grouping: GroupDef = GroupDef()
        self.classifier: List[str] = []
        self.group: int = 0
        self.search: SearchDef = SearchDef()
        self.sorting: List[str] = []
        self._groups = LookupArray[GroupCount](GroupCount, (), GroupCount.keyof)
        self._view_indices: List[int] = []
        self._to_update = True

    def set_sources(self, paths: Sequence[Sequence[str]]) -> None:
        sources = parse_sources(paths)
        if self.sources != sources:
            self.sources = sources
            self._to_update = True

    def set_groups(
        self, field, is_property=None, sorting=None, reverse=None, allow_singletons=None
    ) -> None:
        grouping = parse_grouping(
            field, is_property, sorting, reverse, allow_singletons
        )
        if self.grouping != grouping:
            self.grouping = grouping
            self._to_update = True

    def set_classifier_path(self, path: Sequence[str]) -> None:
        classifier = list(path)
        if self.classifier != classifier:
            self.classifier = classifier
            self._to_update = True

    def set_group(self, group_id) -> None:
        group = max(group_id, 0)
        if self.group != group:
            self.group = group
            self._to_update = True

    def set_search(self, text, cond) -> None:
        search = SearchDef(text, cond)
        if self.search != search:
            self.search = search
            self._to_update = True

    def set_sort(self, sorting) -> None:
        sorting = parse_sorting(sorting)
        if self.sorting != sorting:
            self.sorting = sorting
            self._to_update = True

    def get_sources(self) -> List[List[str]]:
        return self.sources

    def get_grouping(self) -> GroupDef:
        return self.grouping

    def get_classifier_path(self) -> List[str]:
        return self.classifier

    def get_group(self) -> int:
        return self.group

    def get_search(self) -> SearchDef:
        return self.search

    def get_sort(self) -> List[str]:
        return self.sorting

    def reset_parameters(self, *layer_names: str):
        for layer_name in layer_names:
            if layer_name == self.LAYER_SOURCE:
                self.set_sources(())
            elif layer_name == self.LAYER_GROUPING:
                self.set_groups(None)
            elif layer_name == self.LAYER_CLASSIFIER:
                self.set_classifier_path(())
            elif layer_name == self.LAYER_GROUP:
                self.set_group(0)
            elif layer_name == self.LAYER_SEARCH:
                self.set_search("", "")
            elif layer_name == self.LAYER_SORT:
                self.set_sort(())

    def _convert_field_value_to_group_id(self, field_value):
        return self._groups.lookup_index(field_value)

    def _get_classifier_group_value(self, group_id):
        return self._groups[group_id]

    def _force_update(self, *layer_names: str):
        self._to_update = True

    def _get_classifier_stats(self):
        return [{"value": group.value, "count": group.count} for group in self._groups]

    def count_source_videos(self):
        return len(
            {
                video["video_id"]
                for source in self.sources
                for video in self._database.get_videos(
                    include=(), where={flag: True for flag in source}
                )
            }
        )

    def get_view_indices(self) -> Sequence[int]:
        if self._to_update:
            self._update()
            self._to_update = False
        return self._view_indices

    def _update(self):
        pass

    def delete(self, video_id: int):
        self._to_update = True
