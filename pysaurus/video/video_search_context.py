from pysaurus.core.classes import Selector
from pysaurus.database.viewport.view_tools import GroupDef, SearchDef


class VideoSearchContext:
    __slots__ = (
        "sources",
        "grouping",
        "classifier",
        "group_id",
        "search",
        "sorting",
        "selector",
        "page_size",
        "page_number",
        "nb_pages",
        "with_moves",
        "view_count",
        "selection_count",
        "selection_duration",
        "selection_file_size",
        "result_page",
        "result_groups",
    )

    def __init__(
        self,
        *,
        sources=None,
        grouping: GroupDef = None,
        classifier=None,
        group_id=None,
        search: SearchDef = None,
        sorting=None,
        selector: Selector = None,
        page_size: int = None,
        page_number: int = 0,
        with_moves=False,
        result_groups=None,
        result=None,
    ):
        self.sources = sources
        self.grouping = grouping
        self.classifier = classifier
        self.group_id = group_id
        self.search = search
        self.sorting = sorting

        self.selector = selector
        self.page_size = page_size
        self.page_number = page_number
        self.nb_pages = None
        self.with_moves = with_moves

        self.result_groups = result_groups

        self.view_count = 0
        self.selection_count = 0
        self.selection_duration = None
        self.selection_file_size = None
        self.result_page = result