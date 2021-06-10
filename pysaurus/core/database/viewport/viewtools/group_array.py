from pysaurus.core.database.viewport.viewtools.group import Group
from pysaurus.core.database.viewport.viewtools.lookup_array import LookupArray


class GroupArray(LookupArray[Group]):
    __slots__ = ("field",)

    def __init__(self, field: str, content=()):
        super().__init__(Group, content, lambda group: group.field_value)
        self.field = field
