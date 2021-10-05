from typing import List, Optional

from pysaurus.core.classes import ToDict
from pysaurus.core.compare import to_comparable
from pysaurus.core.functions import get_default
from pysaurus.database.viewport.viewtools.group import Group


class GroupDef(ToDict):
    __slots__ = "field", "is_property", "sorting", "reverse", "allow_singletons"
    __print_none__ = True

    FIELD = "field"
    COUNT = "count"
    LENGTH = "length"

    def __init__(
        self,
        field: Optional[str] = None,
        is_property: Optional[bool] = False,
        sorting: Optional[str] = "field",
        reverse: Optional[bool] = False,
        allow_singletons: Optional[bool] = True,
    ):
        self.field = field.strip() if field else None
        self.is_property = bool(is_property)
        self.sorting = sorting.strip() if sorting else self.FIELD
        self.reverse = bool(reverse)
        self.allow_singletons = bool(allow_singletons)
        assert self.sorting in (self.FIELD, self.LENGTH, self.COUNT)

    def __bool__(self):
        return bool(self.field)

    def copy(
        self,
        field=None,
        is_property=None,
        sorting=None,
        reverse=None,
        allow_singletons=None,
    ):
        return GroupDef(
            field=get_default(field, self.field),
            is_property=get_default(is_property, self.is_property),
            sorting=get_default(sorting, self.sorting),
            reverse=get_default(reverse, self.reverse),
            allow_singletons=get_default(allow_singletons, self.allow_singletons),
        )

    def sort(self, groups: List[Group]):
        return self.sort_groups(groups, self.sorting, self.reverse)

    @classmethod
    def sort_groups(cls, groups: List[Group], sorting="field", reverse=False):
        return sorted(
            groups, key=lambda group: cls._comparable_group(group, sorting, reverse)
        )

    @classmethod
    def _comparable_group(cls, group: Group, sorting: str, reverse: bool):
        key = [group.is_defined(), to_comparable(getattr(group, sorting), reverse)]
        if sorting != cls.FIELD:
            key.append(to_comparable(group.field, reverse))
        return key
