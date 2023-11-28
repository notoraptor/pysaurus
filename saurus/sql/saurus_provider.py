from typing import Any, List, Sequence

from pysaurus.core import functions
from pysaurus.database.viewport.abstract_video_provider import AbstractVideoProvider
from pysaurus.database.viewport.view_tools import GroupDef, LookupArray, SearchDef
from pysaurus.video.video_sorting import VideoSorting
from pysaurus.video_provider.provider_utils import parse_sorting, parse_sources
from saurus.sql.grouping_utils import SqlFieldFactory
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
        from saurus.sql.pysaurus_collection import PysaurusCollection

        collection: PysaurusCollection = self._database
        sql_db = collection.db

        if self.search and self.search.cond == "id":
            self._view_indices = [
                row[0]
                for row in sql_db.query(
                    "SELECT video_id FROM video WHERE video_id = ?",
                    [int(self.search.text)],
                )
            ]
            return

        field_factory = SqlFieldFactory(sql_db)
        parser = VideoParser()
        where_parsers = [
            dict(parser(flag, True) for flag in source) for source in self.sources
        ]
        where_group = None
        where_search = None
        params_search = None
        sql_sorting = [
            field_factory.get_sorting(field, reverse)
            for field, reverse in VideoSorting(self.sorting)
        ]
        if self.grouping:
            order_direction = "DESC" if self.grouping.reverse else "ASC"
            without_singletons = ""
            if not self.grouping.allow_singletons:
                without_singletons = "HAVING COUNT(v.video_id) > 1 "
            if self.grouping.is_property:
                if self.grouping.sorting == self.grouping.FIELD:
                    order_field = "v.property_value"
                elif self.grouping.sorting == self.grouping.LENGTH:
                    order_field = "LENGTH(CAST v.property_value AS TEXT)"
                else:
                    assert self.grouping.sorting == self.grouping.COUNT
                    order_field = "COUNT(v.video_id)"
                grouping_where_query = ["p.name = ?"]
                grouping_where_params = [self.grouping.field]
                if self.classifier:
                    grouping_where_query.append(
                        f"v.property_value IN ({','.join(['?'] * len(self.classifier))})"
                    )
                    grouping_where_params.extend(self.classifier)
                grouping_rows = sql_db.query(
                    f"SELECT v.property_value, COUNT(v.video_id) "
                    f"FROM video_property_value AS v JOIN property AS p "
                    f"ON v.property_id = p.property_id "
                    f"WHERE {' AND '.join(grouping_where_query)} "
                    f"GROUP BY v.property_value {without_singletons}"
                    f"ORDER BY {order_field} {order_direction}",
                    grouping_where_params,
                    debug=True,
                )
                nb_fields = 1
            else:
                field = field_factory.get_field(self.grouping.field)
                if self.grouping.sorting == self.grouping.FIELD:
                    order_field = field_factory.get_sorting(
                        self.grouping.field, self.grouping.reverse
                    )
                elif self.grouping.sorting == self.grouping.LENGTH:
                    order_field = (
                        field_factory.get_length(self.grouping.field)
                        + " "
                        + order_direction
                    )
                else:
                    assert self.grouping.sorting == self.grouping.COUNT
                    order_field = f"COUNT(v.video_id) {order_direction}"
                grouping_rows = sql_db.query(
                    f"SELECT {field}, COUNT(v.video_id) "
                    f"FROM video AS v "
                    f"GROUP BY {field} {without_singletons}"
                    f"ORDER BY {order_field}",
                    debug=True,
                )
                nb_fields = field_factory.count_columns(self.grouping.field)
            self._groups.clear()
            self._groups.extend(
                GroupCount(tuple(row[:-1]), row[-1]) for row in grouping_rows
            )
            print("GROUPS:", len(self._groups))
            self.group = min(max(0, self.group), len(self._groups) - 1)
            group = self._groups[self.group]
            where_group = field_factory.get_conditions(self.grouping.field, group.value)
        if self.search:
            tokens = functions.string_to_pieces(self.search.text)
            for i in range(len(tokens)):
                if tokens[i] in ("and", "or"):
                    tokens[i] = f'"{tokens[i]}"'
            if self.search.cond == "and":
                search_placeholders = f"'{' '.join(['?'] * len(tokens))}'"
            elif self.search.cond == "or":
                search_placeholders = f"'{' OR '.join(['?'] * len(tokens))}'"
            else:
                assert self.search.cond == "exact"
                search_placeholders = f"'{' + '.join(['?'] * len(tokens))}'"
            where_search = f"t.content MATCH {search_placeholders}"
            params_search = tokens

        where = ["discarded = 0"]
        params = []
        query = f"SELECT v.video_id FROM video AS v"
        if where_search:
            query += f" JOIN video_text AS t ON v.video_id = t.video_id"
        if where_parsers:
            sqs = []
            for dct in where_parsers:
                keys = list(dct.keys())
                sqs.append(" AND ".join(f"{key} = ?" for key in keys))
                params.extend(dct[key] for key in keys)
            where.append(f"({' OR '.join(f'({sq})' for sq in sqs)})")
        if where_group:
            keys = list(where_group.keys())
            where.append(" AND ".join(f"{key} = ?" for key in keys))
            params.extend(where_group[key] for key in keys)
        if where_search:
            where.append(where_search)
            params.extend(params_search)
        if where:
            query += f" WHERE {' AND '.join(where)}"
        query += f" ORDER BY {', '.join(sql_sorting)}"
        self._view_indices = [row[0] for row in sql_db.query(query, params, debug=True)]

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
