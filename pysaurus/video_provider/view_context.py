"""
ViewContext: pure state management for video view parameters.

Holds the parameters that define a video view (sources, grouping, classifier,
group, search, sorting) and provides mutation methods with cascade logic.

This class is independent of any database — it only manages state.
It is serializable (for web interfaces) and testable without a database.
"""

from typing import Sequence

from pysaurus.core.constants import PYTHON_DEFAULT_SOURCES, VIDEO_DEFAULT_SORTING
from pysaurus.video_provider.provider_utils import parse_sorting, parse_sources
from pysaurus.video_provider.view_tools import GroupDef, SearchDef


class ViewContext:
    __slots__ = ("sources", "grouping", "classifier", "group", "search", "sorting")

    def __init__(self):
        self.sources: list[list[str]] = list(PYTHON_DEFAULT_SOURCES)
        self.grouping: GroupDef = GroupDef()
        self.classifier: list[str] = []
        self.group: int = 0
        self.search: SearchDef = SearchDef()
        self.sorting: list[str] = list(VIDEO_DEFAULT_SORTING)

    def set_sources(self, paths: Sequence[Sequence[str]]) -> None:
        self.sources = parse_sources(paths)

    def set_grouping(
        self,
        field: str | None,
        is_property=None,
        sorting=None,
        reverse=None,
        allow_singletons=None,
    ) -> None:
        self.grouping = GroupDef(field, is_property, sorting, reverse, allow_singletons)
        # Cascade: changing grouping resets classifier, group, and search
        self.classifier = []
        self.group = 0
        self.search = SearchDef()

    def set_group(self, group_id: int) -> None:
        self.group = max(group_id, 0)

    def set_search(self, text: str, cond: str = "and") -> None:
        self.search = SearchDef(text, cond)

    def set_sort(self, sorting: Sequence[str]) -> None:
        self.sorting = parse_sorting(sorting)

    def classifier_select(self, value) -> None:
        """Navigate into the classifier by appending a value to the path."""
        self.classifier = self.classifier + [value]
        self.group = 0

    def classifier_back(self) -> None:
        """Go back one level in the classifier path."""
        self.classifier = self.classifier[:-1]
        self.group = 0

    def classifier_reverse(self) -> list:
        """Reverse the classifier path order. Returns the new path."""
        self.classifier = list(reversed(self.classifier))
        return self.classifier

    def reset(self) -> None:
        """Reset all parameters to defaults."""
        self.__init__()
