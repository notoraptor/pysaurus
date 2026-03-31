from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from pysaurus.core.classes import Selector
from pysaurus.core.constants import VIDEO_DEFAULT_SORTING
from pysaurus.core.duration import Duration
from pysaurus.core.file_size import FileSize
from pysaurus.dbview.field_stat import FieldStat
from pysaurus.dbview.view_tools import GroupDef, SearchDef
from pysaurus.video.video_constants import COMMON_FIELDS, SIMILARITY_FIELDS
from pysaurus.video.video_features import VideoFeatures
from pysaurus.video.video_pattern import VideoPattern
from pysaurus.video.video_sorting import VideoSorting


class DefaultList[T]:
    __slots__ = ("__v",)

    def __init__(self, values: Sequence[T]):
        self.__v = list(values)

    def __call__(self) -> list[T]:
        return list(self.__v)


@dataclass(slots=True)
class VideoSearchContext:
    # Initialization
    sources: Sequence[list[str]] | None = None
    grouping: GroupDef | None = None
    classifier: Sequence[str] | None = None
    group_id: Any = None
    search: SearchDef | None = None
    sorting: Sequence[str] = field(default_factory=DefaultList(VIDEO_DEFAULT_SORTING))
    selector: Selector | None = None
    page_size: int | None = None
    page_number: int = 0
    with_moves: bool = False
    result: list[VideoPattern] = field(default_factory=list)
    # Post-initialization
    nb_pages: int | None = None
    view_count: int = 0
    selection_count: int = 0
    selection_duration: Duration | None = None
    selection_file_size: FileSize | None = None
    # Special fields (?)
    result_groups: Any = None
    classifier_stats: list[FieldStat] = field(default_factory=list)
    common_fields: dict[str, bool] = field(default_factory=dict)
    file_title_diffs: dict[int, list[tuple[int, int]]] = field(default_factory=dict)
    source_count: int = 0

    def __post_init__(self):
        if self.result and self.grouping and self.grouping.field in SIMILARITY_FIELDS:
            self.common_fields = VideoFeatures.get_common_fields(
                self.result, fields=COMMON_FIELDS
            )
            self.file_title_diffs = VideoFeatures.get_file_title_diffs(self.result)

    def grouped_by_moves(self) -> bool:
        return self.grouping is not None and self.grouping.field == "move_id"

    def get_video_sorting(self) -> VideoSorting:
        return VideoSorting(self.sorting)

    def json(self) -> dict:
        grouping = self.grouping
        group_def = (
            grouping.to_dict(
                group_id=self.group_id,
                groups=[st.to_dict() for st in self.classifier_stats],
            )
            if grouping
            else None
        )
        if self.common_fields and group_def is not None:
            group_def["common"] = self.common_fields

        with_moves = self.with_moves
        return {
            "videos": [video.json(with_moves) for video in self.result],
            "pageSize": self.page_size,
            "pageNumber": self.page_number,
            "nbPages": self.nb_pages,
            "nbVideos": self.selection_count,
            "nbViewVideos": self.view_count,
            "validSize": str(self.selection_file_size),
            "validLength": str(self.selection_duration),
            "sources": self.sources,
            "path": self.classifier,
            "searchDef": self.search.to_dict() if self.search else None,
            "sorting": self.sorting,
            "nbSourceVideos": self.source_count,
            "groupDef": group_def,
        }
