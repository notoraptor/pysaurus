from typing import List, Sequence, Tuple

from pysaurus.core.components import AbsolutePath
from saurus.sql.sql_video_wrapper import F


class FieldQuery:
    def __init__(self, field: str, values: Sequence, prefix=""):
        assert values
        self.field = field
        self.values = values
        self.prefix = prefix

    def __str__(self):
        return (
            f"{self.prefix}{'.' if self.prefix else ''}{self.field} "
            f"{'=' if len(self.values) == 1 else 'IN'} "
            f"{'' if len(self.values) == 1 else '('}"
            f"{','.join(['?'] * len(self.values))}"
            f"{'' if len(self.values) == 1 else ')'}"
        )

    __repr__ = __str__

    @classmethod
    def _combine(cls, queries, operand):
        # type: (List[FieldQuery], str) -> Tuple[str, list]
        query_string = f" {operand} ".join(f"({query})" for query in queries)
        query_params = [value for query in queries for value in query.values]
        return query_string, query_params

    @classmethod
    def combine_and(cls, queries):
        return cls._combine(queries, "AND")

    @classmethod
    def combine_or(cls, queries):
        return cls._combine(queries, "OR")

    @classmethod
    def combine_nested_or(cls, super_queries: List[List]):
        query_strings = []
        query_params = []
        for queries in super_queries:
            qs, qp = cls.combine_and(queries)
            query_strings.append(qs)
            query_params.extend(qp)
        query_string = " OR ".join(f"({qs})" for qs in query_strings)
        return f"({query_string})", query_params


class VideoFieldQueryParser:
    __slots__ = ("video_prefix", "thumb_prefix")

    def __init__(self, video_prefix="v", thumb_prefix=""):
        self.video_prefix = video_prefix
        self.thumb_prefix = thumb_prefix

    def parse(self, field, value) -> FieldQuery:
        if hasattr(self, field):
            return getattr(self, field)(value)
        else:
            self._assert_video_table_field(field)
            return self._video_query(field, value)

    def _video_query(self, field, *values):
        return FieldQuery(field, values, self.video_prefix)

    def _thumb_query(self, field, *values):
        return FieldQuery(field, values, self.thumb_prefix)

    @classmethod
    def _assert_video_table_field(cls, value: str) -> str:
        assert getattr(F, value)
        return value

    def video_id(self, value) -> FieldQuery:
        if not isinstance(value, (list, tuple, set)):
            value = [value]
        return self._video_query("video_id", *value)

    def filename(self, value) -> FieldQuery:
        if not isinstance(value, (list, tuple, set)):
            value = [value]
        values = [AbsolutePath.ensure(el).path for el in value]
        return self._video_query("filename", *values)

    def date_entry_modified(self, value) -> FieldQuery:
        return self._video_query("date_entry_modified", float(value))

    def date_entry_opened(self, value) -> FieldQuery:
        return self._video_query("date_entry_opened", float(value))

    def readable(self, value) -> FieldQuery:
        return self._video_query("unreadable", int(not value))

    def found(self, value) -> FieldQuery:
        return self._video_query("is_file", value)

    def not_found(self, value) -> FieldQuery:
        return self._video_query("is_file", int(not value))

    def with_thumbnails(self, value) -> FieldQuery:
        return self._thumb_query("with_thumbnails", int(value))

    def without_thumbnails(self, value) -> FieldQuery:
        return self._thumb_query("with_thumbnails", int(not value))
