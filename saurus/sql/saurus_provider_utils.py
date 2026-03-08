from typing import Any, Iterable, Self

from pysaurus.core import functions
from pysaurus.video_provider.view_tools import SearchDef
from saurus.sql.video_parser import FieldQuery, VideoFieldQueryParser


def get_jointure(field: str) -> str:
    return "" if "(" in field or "v." in field else "v."


def convert_dict_to_sql(dictionary: dict) -> tuple[str, tuple]:
    keys = list(dictionary.keys())
    where = " AND ".join(f"{get_jointure(key)}{key} = ?" for key in keys)
    parameters = tuple(dictionary[key] for key in keys)
    return where, parameters


def convert_dict_series_to_sql(dicts: Iterable[dict]) -> tuple[str, list]:
    query_pieces = []
    params = []
    for dct in dicts:
        sub_query, sub_params = convert_dict_to_sql(dct)
        query_pieces.append(sub_query)
        params.extend(sub_params)
    query = " OR ".join(f"({sq})" for sq in query_pieces)
    return f"({query})", params


def search_to_sql(search: SearchDef) -> tuple[str, list[str]]:
    terms = []
    for piece in functions.string_to_pieces(search.text):
        if piece in ("and", "or"):
            piece = f'"{piece}"'
        terms.append(piece)
    if search.cond == "exact":
        # FTS5 pre-filter with adjacency (+), then LIKE on raw data for
        # precision.  Last term gets prefix * so partial-word matches work
        # (e.g. "Some.Val" finds "Some.Value").  LIKE eliminates false
        # positives (e.g. "Some Valentine").
        exact_phrase = search.text.lower()
        terms[-1] = terms[-1] + "*"
        query = (
            "SELECT vt.rowid FROM video_text AS vt "
            "JOIN video AS v ON v.video_id = vt.rowid "
            "LEFT JOIN video_property_text AS pt ON pt.video_id = v.video_id "
            "WHERE vt.video_text MATCH ? "
            "AND LOWER(v.filename || ' ' || v.meta_title || ' ' || COALESCE(pt.property_text, '')) LIKE ?"
        )
        where = [" + ".join(terms), f"%{exact_phrase}%"]
    else:
        terms = [f"{piece}*" for piece in terms]
        if search.cond == "and":
            query = "SELECT rowid FROM video_text WHERE video_text MATCH ?"
            where = [" ".join(terms)]
        else:
            # search.cond == "or"
            query = "SELECT rowid FROM video_text WHERE video_text MATCH ?"
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
        if self.value is None:
            return None
        return self.value[0] if len(self.value) == 1 else self.value

    def get_printable_value(self):
        value = self.get_value()
        return (
            value
            if value is None or isinstance(value, (str, bool, int, float))
            else str(value)
        )

    @classmethod
    def keyof(cls, group_count: Self) -> Any:
        return group_count.get_value()


_GROUP_DISPLAY_FORMATTERS: dict[str, str] = {
    "audio_bit_rate": "{} Kb/s",
    "audio_bits": "{} bits",
    "bit_depth": "{} bits",
    "channels": "{} ch",
    "frame_rate": "{} fps",
    "sample_rate": "{} Hz",
}


class GroupDisplayFormatter:
    @classmethod
    def audio_bit_rate(cls, value: int) -> str:
        return f"{value / 1000 if value else 0} Kb/s"

    @classmethod
    def audio_bits(cls, value: int) -> str:
        return f"{value or '(0, assumed 32)'} bits"

    @classmethod
    def bit_depth(cls, value: int) -> str:
        return f"{value} bits"

    @classmethod
    def channels(cls, value: int) -> str:
        return f"{value} ch"

    @classmethod
    def frame_rate(cls, value: float) -> str:
        return f"{value or 0} fps"

    @classmethod
    def sample_rate(cls, value: int) -> str:
        return f"{value} Hz"


def format_group_value(field: str, value) -> str:
    """Format a group value for display, matching the video list view style."""
    if value is None:
        return "(No value)"
    formatter = getattr(GroupDisplayFormatter, field, None)
    if formatter is not None:
        return formatter(value)
    return str(value)


class ProviderVideoParser(VideoFieldQueryParser):
    def without_thumbnails(self, value) -> FieldQuery:
        return FieldQuery("IIF(LENGTH(vt.thumbnail), 1, 0)", [int(not value)])

    def with_thumbnails(self, value) -> FieldQuery:
        return FieldQuery("IIF(LENGTH(vt.thumbnail), 1, 0)", [int(value)])
