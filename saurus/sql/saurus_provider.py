from typing import List, Sequence

from pysaurus.core.classes import Selector
from pysaurus.video.video_search_context import VideoSearchContext
from pysaurus.video_provider.abstract_video_provider import AbstractVideoProvider
from pysaurus.video_provider.provider_utils import parse_sorting, parse_sources
from pysaurus.video_provider.view_tools import GroupDef, LookupArray, SearchDef
from saurus.sql.saurus_provider_utils import GroupCount
from saurus.sql.video_mega_search import video_mega_group


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

        self.sources: List[List[str]] = []  #
        self.grouping: GroupDef = GroupDef()  #
        self.classifier: List[str] = []  #
        self.group: int = 0  #
        self.search: SearchDef = SearchDef()  #
        self.sorting: List[str] = []  #

        self._groups = LookupArray[GroupCount](GroupCount, (), GroupCount.keyof)
        self._view_indices: List[int] = []
        self._to_update = True

        self.reset_parameters(*self.LAYERS)

    def _update(self):
        output = video_mega_group(
            self._database.db,
            sources=self.sources,
            grouping=self.grouping,
            classifier=self.classifier,
            group=self.group,
            search=self.search,
            sorting=self.sorting,
            include=["video_id"],
        )
        self.group = output.group_id
        self._groups = output.result_groups
        self._view_indices = [video.video_id for video in output.result_page]

    def get_current_state(
        self, page_size: int, page_number: int, selector: Selector = None
    ) -> VideoSearchContext:
        group_def = self._database.provider.get_group_def()
        grouped_by_moves = group_def and group_def["field"] == "move_id"
        output = video_mega_group(
            self._database.db,
            sources=self.sources,
            grouping=self.grouping,
            classifier=self.classifier,
            group=self.group,
            search=self.search,
            sorting=self.sorting,
            selector=selector,
            page_size=page_size,
            page_number=page_number,
            with_moves=grouped_by_moves,
        )
        self.group = output.group_id
        self._groups = output.result_groups
        self._view_indices = [video["video_id"] for video in output.result_page]
        return output

    def set_sources(self, paths: Sequence[Sequence[str]]) -> None:
        sources = parse_sources(paths)
        if self.sources != sources:
            self.sources = sources
            self._to_update = True

    def set_groups(
        self, field, is_property=None, sorting=None, reverse=None, allow_singletons=None
    ) -> None:
        grouping = GroupDef(field, is_property, sorting, reverse, allow_singletons)
        if self.grouping != grouping:
            self.grouping = grouping
            self._to_update = True
            self.reset_parameters(
                self.LAYER_CLASSIFIER, self.LAYER_GROUP, self.LAYER_SEARCH
            )

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

    def set_search(self, text, cond="and") -> None:
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

    def _convert_field_value_to_group_id(self, field_value):
        return self._groups.lookup_index(field_value)

    def _get_classifier_group_value(self, group_id):
        return self._groups[group_id].get_value()

    def _force_update(self, *layer_names: str):
        self._to_update = True

    def _get_classifier_stats(self):
        return [
            {"value": group.get_printable_value(), "count": group.count}
            for group in self._groups
        ]

    def count_source_videos(self):
        return len(
            {
                video.video_id
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

    def delete(self, video_id: int):
        self._to_update = True
