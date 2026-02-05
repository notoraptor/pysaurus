from typing import Sequence

from pysaurus.core.absolute_path import AbsolutePath
from saurus.sql.sql_video_wrapper import F


class FieldQuery:
    __slots__ = ("table", "field", "values")

    def __init__(self, field: str, values: Sequence, prefix=""):
        if not values:
            raise ValueError(f"FieldQuery requires at least one value for field {field}")
        self.field = field
        self.values = values
        self.table = prefix

    def __str__(self):
        return (
            f"{self.table}{'.' if self.table else ''}{self.field} "
            f"{'=' if len(self.values) == 1 else 'IN'} "
            f"{'' if len(self.values) == 1 else '('}"
            f"{','.join(['?'] * len(self.values))}"
            f"{'' if len(self.values) == 1 else ')'}"
        )

    __repr__ = __str__


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
        if not hasattr(F, value):
            raise ValueError(f"Unknown video field: {value}")
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
        # Use computed expression that works with or without alias
        return FieldQuery("IIF(LENGTH(t.thumbnail), 1, 0)", [int(value)])

    def without_thumbnails(self, value) -> FieldQuery:
        return FieldQuery("IIF(LENGTH(t.thumbnail), 1, 0)", [int(not value)])

    def driver_id(self, value) -> FieldQuery:
        return self._video_query("driver_id", str(value))
