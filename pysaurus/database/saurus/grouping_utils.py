FORMATTED_DURATION_TIME_BASE = "COALESCE(NULLIF(v.duration_time_base, 0), 1)"
SQL_LENGTH = f"(v.duration * 1.0 / {FORMATTED_DURATION_TIME_BASE})"


class SqlField:
    def __init__(self, name: str, definition: list[str], sortable=True):
        if not name or not definition:
            raise ValueError(
                f"SqlField requires name and definition: {name=}, {definition=}"
            )
        self.name = name
        self.definition = definition
        self.sortable = sortable

    def get_field(self) -> str:
        return ", ".join(self.definition)

    def get_length(self) -> str:
        args = ", ',', ".join(self.definition)
        return f"LENGTH(CONCAT({args}))"

    def get_where(self) -> str:
        return " AND ".join(f"{column} = ?" for column in self.definition)

    def get_conditions(self, values: list[str]) -> dict[str, str]:
        return {column: value for column, value in zip(self.definition, values)}

    def get_sorting(self, reverse=False) -> str:
        if not self.sortable:
            raise ValueError(f"Unsortable attribute: {self.name}")
        direction = "DESC" if reverse else "ASC"
        return ", ".join(f"{column} {direction}" for column in self.definition)

    @classmethod
    def auto(cls, name, *, table_name="v", title=None):
        return cls(title or name, [f"{table_name}.{name}"])


class SqlFieldFactory:
    def __init__(self):
        self.fields: dict[str, SqlField] = {
            df.name: df
            for df in (
                SqlField.auto("audio_bit_rate"),
                SqlField.auto("audio_bits"),
                SqlField.auto("audio_codec"),
                SqlField.auto("audio_codec_description"),
                SqlField.auto("bit_depth"),
                SqlField.auto("byte_rate"),
                SqlField.auto("container_format"),
                SqlField.auto("day"),
                SqlField.auto("duration"),
                SqlField.auto("frame_rate"),
                SqlField.auto("filename"),
                SqlField.auto("file_size"),
                SqlField.auto("height"),
                SqlField.auto("sample_rate"),
                SqlField.auto("similarity_id"),
                SqlField.auto("similarity_id_reencoded"),
                SqlField.auto("video_codec"),
                SqlField.auto("video_codec_description"),
                SqlField.auto("video_id"),
                SqlField.auto("watched"),
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
                SqlField("disk", ["v.driver_id"]),
                SqlField.auto("extension"),
                SqlField.auto("file_title"),
                SqlField(
                    "file_title_numeric", ["pysaurus_text_with_numbers(v.file_title)"]
                ),
                SqlField(
                    "filename_numeric", ["pysaurus_text_with_numbers(v.filename)"]
                ),
                SqlField("move_id", ["v.file_size", SQL_LENGTH]),
                SqlField("size_length", ["v.file_size", SQL_LENGTH]),
                SqlField(
                    "title", ["IIF(v.meta_title = '', v.file_title, v.meta_title)"]
                ),
                SqlField(
                    "title_numeric",
                    [
                        "pysaurus_text_with_numbers(IIF(v.meta_title = '', v.file_title, v.meta_title))"
                    ],
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

    def get_conditions(self, name, values: list[str]) -> dict[str, str]:
        return self.fields[name].get_conditions(values)

    def get_sorting(self, name, reverse) -> str:
        return self.fields[name].get_sorting(reverse)
