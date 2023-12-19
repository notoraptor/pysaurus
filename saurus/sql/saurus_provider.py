from typing import Any, Iterable, List, Sequence, Tuple

from pysaurus.core import functions
from pysaurus.database.viewport.abstract_video_provider import AbstractVideoProvider
from pysaurus.database.viewport.view_tools import GroupDef, LookupArray, SearchDef
from pysaurus.video.video_sorting import VideoSorting
from pysaurus.video_provider.provider_utils import parse_sorting, parse_sources
from saurus.sql.grouping_utils import SqlFieldFactory
from saurus.sql.video_parser import VideoParser


def get_jointure(field: str) -> str:
    return "" if "(" in field or "v." in field else "v."


def convert_dict_to_sql(dictionary: dict) -> Tuple[str, Tuple]:
    keys = list(dictionary.keys())
    where = " AND ".join(f"{get_jointure(key)}{key} = ?" for key in keys)
    parameters = tuple(dictionary[key] for key in keys)
    return where, parameters


def convert_dict_series_to_sql(dicts: Iterable[dict]) -> Tuple[str, List]:
    query_pieces = []
    params = []
    for dct in dicts:
        sub_query, sub_params = convert_dict_to_sql(dct)
        query_pieces.append(sub_query)
        params.extend(sub_params)
    query = " OR ".join(f"({sq})" for sq in query_pieces)
    return f"({query})", params


def search_to_sql(search: SearchDef) -> Tuple[str, List[str]]:
    terms = []
    for piece in functions.string_to_pieces(search.text):
        if piece in ("and", "or"):
            piece = f'"{piece}"'
        terms.append(piece)
    if search.cond == "exact":
        query = "SELECT video_id FROM video_text WHERE video_text MATCH ?"
        where = [" + ".join(terms)]
    else:
        terms = [f"{piece}*" for piece in terms]
        if search.cond == "and":
            query = "SELECT video_id FROM video_text WHERE video_text MATCH ?"
            where = [" ".join(terms)]
        else:
            assert search.cond == "or"
            query = "SELECT video_id FROM video_text WHERE video_text MATCH ?"
            where = [" OR ".join(terms)]
    return query, where


class GroupCount:
    __slots__ = ("value", "count")

    def __init__(self, value: tuple, count):
        self.value = value
        self.count = count

    def __str__(self):
        return str((self.value, self.count))

    __repr__ = __str__

    def get_value(self):
        return self.value[0] if len(self.value) == 1 else self.value

    def get_printable_value(self):
        value = self.get_value()
        return (
            value
            if value is None or isinstance(value, (str, bool, int, float))
            else str(value)
        )

    @classmethod
    def keyof(cls, group_count):
        # type: (GroupCount) -> Any
        return group_count.value


class ProviderVideoParser(VideoParser):
    @classmethod
    def without_thumbnails(cls, value) -> Tuple[str, int]:
        return "IIF(LENGTH(vt.thumbnail), 1, 0)", int(not value)

    @classmethod
    def with_thumbnails(cls, value) -> Tuple[str, int]:
        return "IIF(LENGTH(vt.thumbnail), 1, 0)", int(value)


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
        parser = ProviderVideoParser()
        source_query, source_params = convert_dict_series_to_sql(
            dict(parser(flag, True) for flag in source) for source in self.sources
        )
        where_group_query = None
        where_group_params = None
        where_search = None
        params_search = None
        sql_sorting = [
            field_factory.get_sorting(field, reverse)
            for field, reverse in VideoSorting(self.sorting)
        ]
        if self.grouping:
            without_singletons = ""
            if not self.grouping.allow_singletons:
                without_singletons = "HAVING size > 1"
            order_direction = "DESC" if self.grouping.reverse else "ASC"
            if self.grouping.is_property:
                if self.grouping.sorting == self.grouping.FIELD:
                    order_field = "value"
                elif self.grouping.sorting == self.grouping.LENGTH:
                    order_field = "LENGTH(value || '')"
                else:
                    assert self.grouping.sorting == self.grouping.COUNT
                    order_field = "size"

                if self.classifier:
                    placeholders = ["?"] * len(self.classifier)
                    query = f"""
                    SELECT v.video_id
                    FROM video AS v
                    JOIN video_property_value AS vv
                    ON v.video_id = vv.video_id
                    JOIN property AS p
                    ON vv.property_id = p.property_id
                    WHERE
                    v.discarded = 0 AND {source_query} AND p.name = ?
                    AND vv.property_value IN ({','.join(placeholders)})
                    GROUP BY vv.video_id
                    HAVING COUNT(vv.property_value) = ?
                    """
                    params = (
                        source_params
                        + [self.grouping.field]
                        + self.classifier
                        + [len(self.classifier)]
                    )
                    nb_classified_videos = len(sql_db.query_all(query, params))
                    super_query = f"""
                    SELECT xv.property_value AS value, COUNT(x.video_id) AS size
                    FROM
                    (SELECT v.video_id AS video_id
                    FROM video AS v
                    JOIN video_property_value AS vv
                    ON v.video_id = vv.video_id
                    JOIN property AS p
                    ON vv.property_id = p.property_id
                    WHERE
                    v.discarded = 0 AND {source_query} AND p.name = ?
                    AND vv.property_value IN ({','.join(placeholders)})
                    GROUP BY vv.video_id
                    HAVING COUNT(vv.property_value) = ?)                    
                    AS x
                    JOIN video_property_value AS xv ON x.video_id = xv.video_id
                    JOIN property AS xp ON xv.property_id = xp.property_id
                    WHERE xp.name = ? AND value NOT IN ({','.join(placeholders)})
                    GROUP BY value {without_singletons}
                    ORDER BY {order_field} {order_direction}
                    """
                    super_params = params + [self.grouping.field] + self.classifier
                    grouping_rows = [(None, nb_classified_videos)] + sql_db.query_all(
                        super_query, super_params
                    )
                else:
                    super_query = f"""
                    SELECT 
                    IIF(x.have_property = 0, NULL, xv.property_value) AS value, 
                    COUNT(DISTINCT x.video_id) AS size
                    FROM
                    (SELECT 
                    v.video_id AS video_id, 
                    SUM(IIF(p.name = ?, 1, 0)) AS have_property
                    FROM video AS v
                    LEFT JOIN video_property_value AS pv ON v.video_id = pv.video_id
                    LEFT JOIN property AS p ON pv.property_id = p.property_id
                    WHERE v.discarded = 0 AND {source_query}
                    GROUP BY v.video_id)
                    AS x
                    LEFT JOIN video_property_value AS xv ON x.video_id = xv.video_id
                    LEFT JOIN property AS xp ON xv.property_id = xp.property_id
                    WHERE 
                    (x.have_property > 0 AND xp.name = ?) OR (x.have_property = 0)
                    GROUP BY value {without_singletons}
                    ORDER BY {order_field} {order_direction}
                    """
                    super_params = (
                        [self.grouping.field] + source_params + [self.grouping.field]
                    )
                    grouping_rows = sql_db.query(super_query, super_params)
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

                where_similarity_id = ""
                if self.grouping.field == "similarity_id":
                    where_similarity_id = (
                        " AND v.similarity_id IS NOT NULL AND v.similarity_id != -1"
                    )
                grouping_rows = sql_db.query(
                    f"SELECT {field}, COUNT(v.video_id) AS size "
                    f"FROM video AS v "
                    f"WHERE v.discarded = 0 AND {source_query} {where_similarity_id} "
                    f"GROUP BY {field} {without_singletons} "
                    f"ORDER BY {order_field}",
                    source_params,
                )

            self._groups.clear()
            self._groups.extend(
                GroupCount(tuple(row[:-1]), row[-1]) for row in grouping_rows
            )
            if not self._groups:
                self._view_indices = []
                return
            self.group = min(max(0, self.group), len(self._groups) - 1)
            group = self._groups[self.group]
            if self.grouping.is_property:
                (field_value,) = group.value
                if self.classifier:
                    expected = list(self.classifier)
                    if field_value is not None:
                        expected.append(field_value)
                    placeholders = ["?"] * len(expected)
                    query = f"""
                    SELECT v.video_id
                    FROM video_property_value AS v
                    JOIN property AS p
                    ON v.property_id = p.property_id
                    WHERE
                    p.name = ?
                    AND v.property_value IN ({','.join(placeholders)})
                    GROUP BY v.video_id
                    HAVING COUNT(v.property_value) = ?
                    """
                    params = [self.grouping.field] + expected + [len(expected)]
                elif field_value is None:
                    query = f"""
                    SELECT 
                    v.video_id AS video_id
                    FROM video AS v
                    LEFT JOIN video_property_value AS pv ON v.video_id = pv.video_id
                    LEFT JOIN property AS p ON pv.property_id = p.property_id
                    GROUP BY v.video_id HAVING SUM(IIF(p.name = ?, 1, 0)) = 0
                    """
                    params = [self.grouping.field]
                else:
                    query = """
                    SELECT v.video_id FROM video_property_value AS v 
                    JOIN property AS p ON v.property_id = p.property_id 
                    WHERE p.name = ? AND v.property_value = ?
                    """
                    params = [self.grouping.field, field_value]
                where_group_query = f"v.video_id IN ({query})"
                where_group_params = params
            else:
                where_group_query, where_group_params = convert_dict_to_sql(
                    field_factory.get_conditions(self.grouping.field, group.value)
                )
        if self.search:
            where_search, params_search = search_to_sql(self.search)

        query = f"SELECT v.video_id FROM video AS v"
        query += " LEFT JOIN video_thumbnail AS vt ON v.video_id = vt.video_id"
        where = ["v.discarded = 0", source_query]
        params = list(source_params)
        if where_group_query:
            where.append(where_group_query)
            params.extend(where_group_params)
        if where_search:
            where.append(f"v.video_id IN ({where_search})")
            params.extend(params_search)
        query += f" WHERE {' AND '.join(where)} ORDER BY {', '.join(sql_sorting)}"
        self._view_indices = [row[0] for row in sql_db.query(query, params)]

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
        return [
            {"value": group.get_printable_value(), "count": group.count}
            for group in self._groups
        ]

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
