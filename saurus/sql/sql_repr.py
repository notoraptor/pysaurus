from abc import ABC, abstractmethod
from typing import Any

from pysaurus.core.components import AbsolutePath
from pysaurus.core.functions import ensure_list_or_tuple
from saurus.sql.video_parser import FieldQuery


class Table:
    def __init__(self, name: str, short: str = None):
        self.name = name
        self.short = short

    def get_prefix(self) -> str:
        return f"{self.short}." if self.short else ""


class TableField:
    __table_name__ = None
    __public_name__ = None

    def __init__(self, table: Table, name: str = None, public_name: str = None):
        self.table = table
        self.name = name or self.__table_name__
        self.public_name = public_name or self.__public_name__ or self.name

    def code_field(self) -> str:
        return f"{self.table.get_prefix()}{self.name}"

    def parse_value(self, value):
        return value

    def new_field_query(self, value) -> FieldQuery:
        return FieldQuery(
            self.code_field(),
            ensure_list_or_tuple(self.parse_value(value)),
            self.table.short,
        )

    def __str__(self):
        return self.code_field()

    __repr__ = __str__


class VideoID(TableField):
    __table_name__ = "video_id"

    def parse_value(self, value):
        return ensure_list_or_tuple(value)


class Filename(TableField):
    __table_name__ = "filename"

    def parse_value(self, value):
        if not isinstance(value, (list, tuple, set)):
            value = [value]
        return [AbsolutePath.ensure(el).path for el in value]


class DateEntryModified(TableField):
    __table_name__ = "date_entry_modified"

    def parse_value(self, value):
        return float(value)


class DateEntryOpened(DateEntryModified):
    __table_name__ = "date_entry_opened"


class Readable(TableField):
    __public_name__ = "readable"
    __table_name__ = "unreadable"

    def parse_value(self, value):
        return int(not value)


class Found(TableField):
    __public_name__ = "found"
    __table_name__ = "is_file"


class NotFound(TableField):
    __public_name__ = "not_found"
    __table_name__ = "is_file"

    def parse_value(self, value):
        return int(not value)


class WithThumbnails(TableField):
    """Table thumbnail"""

    __public_name__ = "with_thumbnails"
    __table_name__ = "thumbnail"

    def code_field(self) -> str:
        field_thumbnail = super().code_field()
        return f"IIF(LENGTH({field_thumbnail}), 1, 0)"

    def parse_value(self, value):
        return int(value)


class WithoutThumbnails(WithThumbnails):
    """Table thumbnail"""

    __public_name__ = "without_thumbnails"

    def parse_value(self, value):
        return int(not value)


class VideoDate(TableField):
    __public_name__ = "date"
    __table_name__ = "mtime"


class VideoDat(TableField):
    __public_name__ = "day"
    __table_name__ = "mtime"

    def code_field(self) -> str:
        f_mtime = super().code_field()
        return f"strftime('%Y-%m-%d', datetime({f_mtime}, 'unixepoch'))"


class _FormattedDurationTimeBase(TableField):
    __table_name__ = "duration_time_base"

    def code_field(self) -> str:
        f_duration_time_base = super().code_field()
        return f"COALESCE(NULLIF({f_duration_time_base}, 0), 1)"


class DatabaseField(ABC):
    __slots__ = ("name", "_definition", "_sortable")

    def __init__(self, name: str, sortable=True):
        self.name = name
        self._definition: list[str] | None = None
        self._sortable = sortable

    @property
    def definition(self) -> list[str]:
        if self._definition is None:
            self._definition = self._code_definition()
        return self._definition

    @abstractmethod
    def _code_definition(self) -> list[str]:
        raise NotImplementedError()

    def code_length(self) -> str:
        if len(self.definition) > 1:
            raise ValueError(
                f"Cannot get length of attribute with multiple columns: {self.name}"
            )
        return f"LENGTH(CONCAT({self.definition[0]}))"

    def code_where(self) -> str:
        return " AND ".join(f"{column} = ?" for column in self.definition)

    def code_sorting(self, reverse=False) -> str:
        if not self._sortable:
            raise ValueError(f"Cannot sort attribute: {self.name}")
        direction = "DESC" if reverse else "ASC"
        return ", ".join(f"{column} {direction}" for column in self.definition)

    def get_conditions(self, values: list[Any]) -> dict[str, Any]:
        return {column: value for column, value in zip(self.definition, values)}


class _VideoLength(DatabaseField):
    def __init__(
        self, duration: TableField, duration_time_base: _FormattedDurationTimeBase
    ):
        super().__init__("length")
        self.duration = duration
        self.duration_time_base = duration_time_base

    def _code_definition(self) -> list[str]:
        f_duration = self.duration.code_field()
        f_duration_time_base = self.duration_time_base.code_field()
        return [f"({f_duration} * 1.0 / {f_duration_time_base})"]


class _BitRate(DatabaseField):
    def __init__(
        self,
        duration: TableField,
        file_size: TableField,
        duration_time_base: _FormattedDurationTimeBase,
    ):
        super().__init__("bit_rate")
        self.duration = duration
        self.file_size = file_size
        self.duration_time_base = duration_time_base

    def _code_definition(self) -> list[str]:
        f_file_size = self.file_size.code_field()
        f_duration = self.duration.code_field()
        f_duration_time_base = self.duration_time_base.code_field()
        return [
            f"IIF({f_duration} = 0, 0, {f_file_size} * {f_duration_time_base} / {f_duration})"
        ]


class _DateEntryModified(DatabaseField):
    def __init__(self, date_entry_modified: TableField, mtime: TableField):
        super().__init__("date_entry_modified")
        self.date_entry_modified = date_entry_modified
        self.mtime = mtime

    def _code_definition(self) -> list[str]:
        f_date_entry_modified = self.date_entry_modified.code_field()
        f_mtime = self.mtime.code_field()
        return [f"COALESCE({f_date_entry_modified}, {f_mtime})"]


class _DateEntryOpened(DatabaseField):
    def __init__(self, date_entry_opened: TableField, mtime: TableField):
        super().__init__("date_entry_opened")
        self.date_entry_opened = date_entry_opened
        self.mtime = mtime

    def _code_definition(self) -> list[str]:
        f_date_entry_opened = self.date_entry_opened.code_field()
        f_mtime = self.mtime.code_field()
        return [f"COALESCE({f_date_entry_opened}, {f_mtime})"]


class CombinedFields:
    @staticmethod
    def disk(filename: TableField, driver_id: TableField) -> list[str]:
        return [f"pysaurus_get_disk({filename}, {driver_id})"]


class DatabaseTableField(DatabaseField):
    __slots__ = ("table_field",)

    def __init__(self, table_field: TableField, sortable=True):
        self.table_field = table_field
        super().__init__(table_field.name, sortable=sortable)

    def _code_definition(self) -> list[str]:
        return [self.table_field.code_field()]
