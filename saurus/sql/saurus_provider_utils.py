from typing import Any, Iterable, List, Tuple

from pysaurus.core import functions
from pysaurus.video_provider.view_tools import SearchDef
from saurus.sql.video_parser import FieldQuery, VideoFieldQueryParser


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
        return group_count.get_value()


class ProviderVideoParser(VideoFieldQueryParser):
    def without_thumbnails(self, value) -> FieldQuery:
        return FieldQuery("IIF(LENGTH(vt.thumbnail), 1, 0)", [int(not value)])

    def with_thumbnails(self, value) -> FieldQuery:
        return FieldQuery("IIF(LENGTH(vt.thumbnail), 1, 0)", [int(value)])
