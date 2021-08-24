from typing import Iterable

from pysaurus.database.viewport.viewtools.group import Group
from pysaurus.database.viewport.viewtools.lookup_array import LookupArray


class GroupArray(LookupArray[Group]):
    __slots__ = "field", "is_property"

    def __init__(self, field: str, is_property: bool, content: Iterable[Group]):
        super().__init__(Group, content, lambda group: group.field_value)
        self.field = field
        self.is_property = is_property
