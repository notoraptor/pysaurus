from typing import Dict, List

from pysaurus.core.semantic_text import get_longest_number_in_string
from saurus.sql.pysaurus_connection import PysaurusConnection

FORMATTED_DURATION_TIME_BASE = "COALESCE(NULLIF(v.duration_time_base, 0), 1)"
SQL_LENGTH = f"(v.duration * 1.0 / {FORMATTED_DURATION_TIME_BASE})"


class SqlField:
    def __init__(self, name: str, definition: List[str], sortable=True):
        assert name and definition
        self.name = name
        self.definition = definition
        self.sortable = sortable

    def get_field(self) -> str:
        return ", ".join(self.definition)

    def get_length(self):
        if len(self.definition) > 1:
            raise ValueError(
                f"Cannot get length of attribute with multiple columns: {self.name}"
            )
        return f"LENGTH(CONCAT({self.definition[0]}))"

    def get_where(self) -> str:
        return " AND ".join(f"{column} = ?" for column in self.definition)

    def get_conditions(self, values: List) -> dict:
        return {column: value for column, value in zip(self.definition, values)}

    def get_sorting(self, reverse=False) -> str:
        if not self.sortable:
            raise ValueError(f"Unsortable attribute: {self.name}")
        direction = "DESC" if reverse else "ASC"
        return ", ".join(f"{column} {direction}" for column in self.definition)

    @classmethod
    def auto(cls, name, *, table_name="v", title=None):
        return cls(title or name, [f"{table_name}.{name}"])


class SemanticField(SqlField):
    def __init__(self, name: str, field: str, padding: int, sortable=True):
        field = field.format(padding=padding)
        super().__init__(name, [field], sortable)


class SqlFieldFactory:
    def __init__(self, connection: PysaurusConnection):
        padding_filenames = max(
            (
                get_longest_number_in_string(row[0])
                for row in connection.query("SELECT filename FROM video")
            ),
            default=0,
        )
        padding_meta_titles = max(
            (
                get_longest_number_in_string(row[0])
                for row in connection.query(
                    "SELECT meta_title FROM video WHERE meta_title != ''"
                )
            ),
            default=0,
        )
        padding = max(padding_filenames, padding_meta_titles)
        self.connection = connection
        self.fields: Dict[str, SqlField] = {
            df.name: df
            for df in (
                SqlField.auto("audio_bit_rate"),
                SqlField.auto("audio_bits"),
                SqlField.auto("audio_codec"),
                SqlField.auto("audio_codec_description"),
                SqlField.auto("bit_depth"),
                SqlField.auto("bit_rate"),
                SqlField.auto("container_format"),
                SqlField.auto("day"),
                SqlField.auto("frame_rate"),
                SqlField.auto("filename"),
                SqlField.auto("file_size"),
                SqlField.auto("height"),
                SqlField.auto("sample_rate"),
                SqlField.auto("similarity_id"),
                SqlField.auto("video_codec"),
                SqlField.auto("video_codec_description"),
                SqlField.auto("width"),
                SqlField.auto("year"),
                SqlField.auto(title="date", name="mtime"),
                SqlField.auto(title="size", name="file_size"),
                SqlField.auto(
                    title="date_entry_modified", name="date_entry_modified_not_null"
                ),
                SqlField.auto(
                    title="date_entry_opened", name="date_entry_opened_not_null"
                ),
                SqlField.auto(title="length", name="length_seconds"),
                # Special fields
                SqlField("disk", ["pysaurus_get_disk(v.filename, v.driver_id)"]),
                SqlField("extension", ["pysaurus_get_extension(v.filename)"]),
                SqlField("file_title", ["pysaurus_get_file_title(v.filename)"]),
                SemanticField(
                    "file_title_numeric",
                    "pysaurus_text_with_numbers(pysaurus_get_file_title(v.filename), {padding})",
                    padding,
                ),
                SemanticField(
                    "filename_numeric",
                    "pysaurus_text_with_numbers(v.filename, {padding})",
                    padding,
                ),
                SqlField("move_id", ["v.file_size", SQL_LENGTH]),
                SqlField("size_length", ["v.file_size", SQL_LENGTH]),
                SqlField("title", ["pysaurus_get_title(v.filename, v.meta_title)"]),
                SemanticField(
                    "title_numeric",
                    "pysaurus_text_with_numbers(pysaurus_get_title(v.filename, v.meta_title), {padding})",
                    padding,
                ),
            )
        }

    def count_columns(self, name) -> int:
        return len(self.fields[name].definition)

    def get_field(self, name) -> str:
        return self.fields[name].get_field()

    def get_length(self, name) -> str:
        return self.fields[name].get_length()

    def get_where(self, name) -> str:
        return self.fields[name].get_where()

    def get_conditions(self, name, values: List) -> dict:
        return self.fields[name].get_conditions(values)

    def get_sorting(self, name, reverse) -> str:
        return self.fields[name].get_sorting(reverse)
