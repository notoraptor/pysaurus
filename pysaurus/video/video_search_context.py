from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from pysaurus.core.classes import Selector
from pysaurus.core.components import FileSize
from pysaurus.core.duration import Duration
from pysaurus.video.video_constants import COMMON_FIELDS
from pysaurus.video.video_features import VideoFeatures
from pysaurus.video.video_pattern import VideoPattern
from pysaurus.video_provider.field_stat import FieldStat
from pysaurus.video_provider.view_tools import GroupDef, SearchDef


@dataclass(slots=True)
class VideoSearchContext:
    # Initialization
    sources: Sequence[list[str]] | None = None
    grouping: GroupDef | None = None
    classifier: Sequence[str] | None = None
    group_id: Any = None
    search: SearchDef = None
    sorting: Sequence[str] = None
    selector: Selector = None
    page_size: int = None
    page_number: int = 0
    with_moves: bool = False
    result: list[VideoPattern] | None = None
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
    source_count: int = 0

    def __post_init__(self):
        if self.result and self.grouping.field == "similarity_id":
            self.common_fields = VideoFeatures.get_common_fields(
                self.result, fields=COMMON_FIELDS
            )

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
        if self.common_fields:
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
