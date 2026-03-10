from typing import Iterable

from pysaurus.core.classes import ToDict
from pysaurus.core.compare import NegativeComparator
from pysaurus.core.enumeration import Enumeration
from pysaurus.core.functions import get_default, identity
from pysaurus.core.lookup_array import LookupArray


class Group:
    __slots__ = ("field_value", "videos")

    def __init__(self, field_value=None, videos: Iterable[int] = ()):
        self.field_value = field_value
        self.videos = videos if isinstance(videos, set) else set(videos)

    def is_defined(self):
        return self.field_value is not None

    @property
    def field(self):
        return self.field_value

    @property
    def length(self):
        return len(str(self.field_value))

    @property
    def count(self):
        return len(self.videos)


class GroupArray(LookupArray[Group]):
    __slots__ = "field", "is_property"

    def __init__(self, field: str, is_property: bool, content: Iterable[Group]):
        super().__init__(Group, content, lambda group: group.field_value)
        self.field = field
        self.is_property = is_property


class GroupDef(ToDict):
    __slots__ = (
        "field",
        "is_property",
        "sorting",
        "reverse",
        "allow_singletons",
        "_int_reverse",
        "_fn_reverse",
    )
    __print_none__ = True
    __props__ = ("field", "is_property", "sorting", "reverse", "allow_singletons")

    FIELD = "field"
    COUNT = "count"
    LENGTH = "length"

    def __init__(
        self,
        field: str | None = None,
        is_property: bool | None = False,
        sorting: str | None = FIELD,
        reverse: bool | None = False,
        allow_singletons: bool | None = True,
    ):
        self.field = (field and field.strip()) or None
        self.is_property = bool(is_property)
        self.sorting = sorting.strip() if sorting else self.FIELD
        self.reverse = bool(reverse)
        self.allow_singletons = bool(allow_singletons)

        self._int_reverse = -1 if self.reverse else 1
        self._fn_reverse = NegativeComparator if self.reverse else identity
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

    def _generate_sort_key(self):
        if self.sorting == self.FIELD:
            return lambda group: (
                group.field_value is not None,
                self._fn_reverse(group.field_value),
            )
        else:
            # If sorting is not field, we will use group field
            # to sort groups with same sorting value.
            return lambda group: (
                group.field_value is not None,
                getattr(group, self.sorting) * self._int_reverse,
                self._fn_reverse(group.field_value),
            )

    def sorted(self, groups: Iterable[Group]) -> list[Group]:
        return sorted(groups, key=self._generate_sort_key())

    def sort_inplace(self, groups: list[Group]):
        groups.sort(key=self._generate_sort_key())


class SearchDef(ToDict):
    __slots__ = "text", "cond"
    __print_none__ = True
    _Cond = Enumeration(("and", "or", "exact", "id"))

    def __init__(self, text: str | None = None, cond: str | None = None):
        self.text = text.strip() if text else None
        self.cond = self._Cond((cond and cond.strip()) or "and")

    def __bool__(self):
        return bool(self.text)
