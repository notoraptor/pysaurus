from enum import IntEnum
from typing import Any

from pysaurus.video_provider.view_tools import GroupDef


class GroupPerm(IntEnum):
    FORBIDDEN = 0
    ONLY_MANY = 1
    ALL = 2


class FieldType(IntEnum):
    BOOL = 0
    INT = 1
    FLOAT = 2
    STR = 3
    SORTABLE = 4
    UNSORTABLE = 5


class FieldInfo:
    def __init__(
        self,
        name: str,
        title: str = None,
        group_permission: GroupPerm = GroupPerm.ALL,
        field_type: FieldType = FieldType.STR,
    ):
        self.name = name
        self.title = title or name.replace("_", " ")
        self.group_permission = group_permission
        self.field_type = field_type

    def _key(self) -> tuple:
        return self.name, self.title, self.group_permission, self.field_type

    def __repr__(self):
        return repr(self._key())

    def __hash__(self) -> int:
        return hash(self._key())

    def __eq__(self, other) -> bool:
        return isinstance(other, FieldInfo) and self._key() == other._key()

    def is_forbidden(self) -> bool:
        return self.group_permission == GroupPerm.FORBIDDEN

    def is_only_many(self) -> bool:
        return self.group_permission == GroupPerm.ONLY_MANY

    def is_all(self) -> bool:
        return self.group_permission == GroupPerm.ALL

    def is_string(self) -> bool:
        return self.field_type == FieldType.STR

    def is_sortable(self) -> bool:
        return self.field_type != FieldType.UNSORTABLE


class FieldMap:
    def __init__(self, field_info_list: list[FieldInfo]):
        self.list = field_info_list
        self.allowed: list[FieldInfo] = []
        self.sortable: list[FieldInfo] = []
        self.fields: dict[str, FieldInfo] = {}

        for field_info in field_info_list:
            if field_info.name in self.fields:
                raise ValueError(f"Duplicated field: {field_info.name}")
            self.fields[field_info.name] = field_info
            if not field_info.is_forbidden():
                self.allowed.append(field_info)
            if field_info.is_sortable():
                self.sortable.append(field_info)

        self.list.sort(key=self._compare_field_info)
        self.allowed.sort(key=self._compare_field_info)

    @staticmethod
    def _compare_field_info(field_info: FieldInfo) -> tuple:
        return field_info.title, field_info.name

    def get_title(self, field: str) -> str:
        return self.fields[field].title


FIELD_MAP = FieldMap(
    [
        FieldInfo("audio_bit_rate", "audio bit rate", GroupPerm.ALL, FieldType.INT),
        FieldInfo("audio_bits", "audio bits per sample", GroupPerm.ALL, FieldType.INT),
        FieldInfo("audio_codec", "audio codec", GroupPerm.ALL, FieldType.STR),
        FieldInfo("audio_codec_description", None, GroupPerm.ALL, FieldType.STR),
        FieldInfo("bit_rate", "bit rate", GroupPerm.ONLY_MANY, FieldType.SORTABLE),
        FieldInfo("bit_depth", "bit depth", GroupPerm.ALL, FieldType.INT),
        FieldInfo("container_format", None, GroupPerm.ALL, FieldType.STR),
        FieldInfo("date", "date modified", GroupPerm.ONLY_MANY, FieldType.SORTABLE),
        FieldInfo("date_entry_modified", None, GroupPerm.ONLY_MANY, FieldType.SORTABLE),
        FieldInfo("date_entry_opened", None, GroupPerm.ONLY_MANY, FieldType.SORTABLE),
        FieldInfo("day", "day", GroupPerm.ALL, FieldType.STR),
        FieldInfo("disk", "disk", GroupPerm.ALL, FieldType.STR),
        FieldInfo("extension", "file extension", GroupPerm.ALL, FieldType.STR),
        FieldInfo("file_size", "file size (bytes)", GroupPerm.ONLY_MANY, FieldType.INT),
        FieldInfo("file_title", "file title", GroupPerm.ONLY_MANY, FieldType.STR),
        FieldInfo(
            "file_title_numeric",
            "file title (with numbers)",
            GroupPerm.ONLY_MANY,
            FieldType.SORTABLE,
        ),
        FieldInfo("filename", "file path", GroupPerm.ONLY_MANY, FieldType.STR),
        FieldInfo(
            "filename_length", "file path length", GroupPerm.FORBIDDEN, FieldType.INT
        ),
        FieldInfo(
            "filename_numeric",
            "file path (with numbers)",
            GroupPerm.ONLY_MANY,
            FieldType.SORTABLE,
        ),
        FieldInfo("frame_rate", "frame rate", GroupPerm.ALL, FieldType.FLOAT),
        FieldInfo("height", "height", GroupPerm.ALL, FieldType.INT),
        FieldInfo("length", "length", GroupPerm.ONLY_MANY, FieldType.SORTABLE),
        FieldInfo(
            "move_id",
            "moved files (potentially)",
            GroupPerm.ONLY_MANY,
            FieldType.UNSORTABLE,
        ),
        FieldInfo("properties", None, GroupPerm.FORBIDDEN, FieldType.UNSORTABLE),
        FieldInfo("sample_rate", "sample rate", GroupPerm.ALL, FieldType.INT),
        FieldInfo(
            "similarity_id", "similarity", GroupPerm.ONLY_MANY, FieldType.UNSORTABLE
        ),
        FieldInfo("size", "size", GroupPerm.ONLY_MANY, FieldType.SORTABLE),
        FieldInfo(
            "size_length", "(size and length)", GroupPerm.ONLY_MANY, FieldType.SORTABLE
        ),
        FieldInfo("thumbnail_path", None, GroupPerm.FORBIDDEN, FieldType.UNSORTABLE),
        FieldInfo("title", "title", GroupPerm.ONLY_MANY, FieldType.STR),
        FieldInfo(
            "title_numeric",
            "title (with numbers)",
            GroupPerm.ONLY_MANY,
            FieldType.SORTABLE,
        ),
        FieldInfo("video_codec", "video codec", GroupPerm.ALL, FieldType.STR),
        FieldInfo("video_codec_description", None, GroupPerm.ALL, FieldType.STR),
        FieldInfo("video_id", "video ID", GroupPerm.FORBIDDEN, FieldType.INT),
        FieldInfo("watched", "watched", GroupPerm.ALL, FieldType.BOOL),
        FieldInfo("width", "width", GroupPerm.ALL, FieldType.INT),
        FieldInfo("year", "year", GroupPerm.ALL, FieldType.INT),
    ]
)

SOURCE_TREE = {
    "unreadable": {"not_found": False, "found": False},
    "readable": {
        "not_found": {"with_thumbnails": False, "without_thumbnails": False},
        "found": {"with_thumbnails": False, "without_thumbnails": False},
    },
}

SEARCH_COND_TITLE = {
    "exact": "exactly",
    "and": "all terms",
    "or": "any term",
    "id": "video ID",
}


class Uniconst:
    CROSS = "\u2715"
    SETTINGS = "\u2630"
    ARROW_DOWN = "\u25bc"
    ARROW_UP = "\u25b2"
    SMART_ARROW_LEFT = "\u2b9c"
    SMART_ARROW_RIGHT = "\u2b9e"
    WARNING_SIGN = "\u26a0"  # ⚠
    JAPANESE_SINGLE_QUOTATION_START = "「"
    JAPANESE_SINGLE_QUOTATION_END = "」"
    JAPANESE_DOUBLE_QUOTATION_START = "『"
    JAPANESE_DOUBLE_QUOTATION_END = "』"
    DOUBLE_BAR = "‖"

    QUOTATION_MARKS = (
        ("«", "»"),
        (JAPANESE_SINGLE_QUOTATION_START, JAPANESE_SINGLE_QUOTATION_END),
        (JAPANESE_DOUBLE_QUOTATION_START, JAPANESE_DOUBLE_QUOTATION_END),
        ("“", "”"),
        ("[", "]"),
        ('"', '"'),
        ("'", "'"),
        ("(", ")"),
    )


def pretty_quote(text: Any) -> str:
    if not isinstance(text, str):
        text = str(text)
    for mark_left, mark_right in Uniconst.QUOTATION_MARKS:
        if mark_left not in text and mark_right not in text:
            return f"{mark_left}{text}{mark_right}"
    else:
        return repr(text)


def pretty_grouping(grouping: GroupDef) -> str:
    title = (
        pretty_quote(FIELD_MAP.get_title(grouping.field))
        + " "
        + (Uniconst.ARROW_DOWN if grouping.reverse else Uniconst.ARROW_UP)
    )
    if grouping.is_property:
        title = f"property: {title}"
    if grouping.sorting == grouping.LENGTH:
        title = f"{Uniconst.DOUBLE_BAR} {title} {Uniconst.DOUBLE_BAR}"
    elif grouping.sorting == grouping.COUNT:
        title = f"# {title}"
    if grouping.allow_singletons:
        title = f"many {title}"
    return title
