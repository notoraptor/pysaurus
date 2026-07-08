"""
ViewContext: pure state management for video view parameters.

Holds the parameters that define a video view (sources, grouping, classifier,
group, search, sorting) and provides mutation methods with cascade logic.

This class is independent of any database — it only manages state.
It is serializable (for web interfaces) and testable without a database.
"""

from typing import Sequence

from pysaurus.application.exceptions import PysaurusError
from pysaurus.core.constants import PYTHON_DEFAULT_SOURCES, VIDEO_DEFAULT_SORTING
from pysaurus.dbview.view_tools import GroupDef, SearchDef
from pysaurus.dbview.view_utils import parse_sorting, parse_sources


class ViewContext:
    __slots__ = (
        "sources",
        "source_expression",
        "grouping",
        "classifier",
        "group",
        "search",
        "sorting",
        "_generation",
    )

    def __init__(self):
        self.sources: list[list[str]] = list(PYTHON_DEFAULT_SOURCES)
        self.source_expression: str | None = None
        self.grouping: GroupDef = GroupDef()
        self.classifier: list[str] = []
        self.group: int = 0
        self.search: SearchDef = SearchDef()
        self.sorting: list[str] = list(VIDEO_DEFAULT_SORTING)
        self._generation: int = 0

    @property
    def generation(self) -> int:
        """Bumped by every mutation that changes which videos are in the view
        (sources, search, grouping, group, classifier, reset). Sorting is
        excluded: it reorders the view but never changes its membership.

        Interfaces can cache the last generation they observed and compare it
        on each refresh to know when a cross-page/cross-view video selection
        is no longer valid, without duplicating the "what counts as a view
        change" rule in each interface.
        """
        return self._generation

    def _bump(self) -> None:
        self._generation += 1

    def set_sources(self, paths: Sequence[Sequence[str]]) -> None:
        self.sources = parse_sources(paths)
        self.source_expression = None
        self._bump()

    def set_source_expression(self, expression: str | None) -> None:
        self.source_expression = expression.strip() if expression else None
        self._bump()

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
        self._bump()

    def set_group(self, group_id: int) -> None:
        self.group = max(group_id, 0)
        self._bump()

    def set_search(self, text: str, cond: str = "and") -> None:
        try:
            self.search = SearchDef(text, cond)
        except ValueError as exc:
            raise PysaurusError(str(exc))
        self._bump()

    def set_sort(self, sorting: Sequence[str]) -> None:
        self.sorting = parse_sorting(sorting)

    def classifier_select(self, value) -> None:
        """Navigate into the classifier by appending a value to the path."""
        self.classifier = self.classifier + [value]
        self.group = 0
        self._bump()

    def classifier_back(self) -> None:
        """Go back one level in the classifier path."""
        self.classifier = self.classifier[:-1]
        self.group = 0
        self._bump()

    def classifier_reverse(self) -> list:
        """Reverse the classifier path order. Returns the new path."""
        self.classifier = list(reversed(self.classifier))
        self._bump()
        return self.classifier

    def classifier_clear(self) -> None:
        """Clear the classifier path (e.g. after concatenating it into a property)."""
        self.classifier = []
        self.group = 0
        self._bump()

    def reset(self) -> None:
        """Reset all parameters to defaults."""
        generation = self._generation
        self.__init__()
        # Monotonic: never re-use a generation an interface may already have seen.
        self._generation = generation + 1
