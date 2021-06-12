from typing import Optional, List

from pysaurus.core.classes import ToFulLDict, NegativeComparator
from pysaurus.core.database.viewport.viewtools.group import Group


class GroupDef(ToFulLDict):
    __slots__ = "field", "sorting", "reverse", "allow_singletons", "allow_multiple"

    FIELD = "field"
    LENGTH = "length"
    COUNT = "count"

    def __init__(
        self,
        field: Optional[str],
        sorting: Optional[str] = "field",
        reverse: Optional[bool] = False,
        allow_singletons: Optional[bool] = False,
        allow_multiple: Optional[bool] = True,
    ):
        self.field = field.strip() if field else None
        self.sorting = sorting.strip() if sorting else None
        self.reverse = bool(reverse)
        self.allow_singletons = bool(allow_singletons)
        self.allow_multiple = bool(allow_multiple)
        assert self.sorting in (self.FIELD, self.LENGTH, self.COUNT)

    def __bool__(self):
        return bool(self.field)

    def copy(
        self,
        field=None,
        sorting=None,
        reverse=None,
        allow_singletons=None,
        allow_multiple=None,
    ):
        field = field if field is not None else self.field
        sorting = sorting if sorting is not None else self.sorting
        reverse = reverse if reverse is not None else self.reverse
        allow_singletons = (
            allow_singletons if allow_singletons is not None else self.allow_singletons
        )
        allow_multiple = (
            allow_multiple if allow_multiple is not None else self.allow_multiple
        )
        return GroupDef(field, sorting, reverse, allow_singletons, allow_multiple)

    def sort(self, groups):
        # type: (List[Group]) -> List[Group]
        return self.sort_groups(groups, self.field, self.sorting, self.reverse)

    @classmethod
    def sort_groups(cls, groups, field, sorting="field", reverse=False):
        # type: (List[Group], str, str, bool) -> List[Group]
        none_group = None
        other_groups = []
        for group in groups:
            if group.field_value is None:
                assert none_group is None
                none_group = group
            else:
                other_groups.append(group)
        if sorting == cls.FIELD:
            key = lambda group: cls.make_comparable(group.field_value, reverse)
        elif sorting == cls.COUNT:
            key = lambda group: (
                cls.make_comparable(len(group.videos), reverse),
                cls.make_comparable(group.field_value, reverse),
            )
        else:
            assert sorting == cls.LENGTH
            key = lambda group: (
                cls.make_comparable(len(str(group.field_value)), reverse),
                cls.make_comparable(group.field_value, reverse),
            )
        other_groups.sort(key=key)
        return ([none_group] + other_groups) if none_group else other_groups

    @classmethod
    def make_comparable(cls, value, reverse):
        return NegativeComparator(value) if reverse else value
