from typing import Any, List, Sequence

from pysaurus.database.viewport.abstract_video_provider import AbstractVideoProvider
from pysaurus.database.viewport.view_tools import GroupDef, LookupArray, SearchDef
from pysaurus.video_provider.provider_utils import parse_sorting, parse_sources
from saurus.sql.video_parser import VideoParser


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

    def _update(self):
        from saurus.sql.pysaurus_collection import PysaurusCollection

        collection: PysaurusCollection = self._database
        sql_db = collection.db

        parser = VideoParser()
        where_parsers = [
            dict(parser(flag, True) for flag in source) for source in self.sources
        ]
        if self.grouping:
            order_direction = "DESC" if self.grouping.reverse else "ASC"
            if self.grouping.sorting == self.grouping.FIELD:
                order_field = "v.property_value"
            elif self.grouping.sorting == self.grouping.LENGTH:
                order_field = "LENGTH(CAST v.property_value AS TEXT)"
            else:
                assert self.grouping.sorting == self.grouping.COUNT
                order_field = "COUNT(v.video_id)"
            without_singletons = ""
            if not self.grouping.allow_singletons:
                without_singletons = "HAVING COUNT(v.video_id) > 1 "
            if self.grouping.is_property:
                sql_db.query(
                    f"SELECT v.property_value, COUNT(v.video_id) "
                    f"FROM video_property_value AS v JOIN property AS p "
                    f"ON v.property_id = p.property_id "
                    f"WHERE p.name = ? "
                    f"GROUP BY v.property_value {without_singletons}"
                    f"ORDER BY {order_field} {order_direction}",
                    [self.grouping.field],
                )
            else:
                field = ""
                sql_db.query(
                    f"SELECT {field}, COUNT(v.video_id) "
                    f"FROM video AS v "
                    f"GROUP BY {field} {without_singletons}"
                    f"ORDER BY {order_field} {order_direction}"
                )

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

    def delete(self, video_id: int):
        self._to_update = True
