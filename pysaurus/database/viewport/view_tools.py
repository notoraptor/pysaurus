from abc import abstractmethod
from typing import Iterable, List, Optional, Sequence

from pysaurus.core.classes import ToDict
from pysaurus.core.compare import to_comparable
from pysaurus.core.enumeration import Enumeration
from pysaurus.core.functions import get_default
from pysaurus.core.lookup_array import LookupArray
from pysaurus.video import Video
from pysaurus.video.fake_video import FakeVideo


class VideoArray(LookupArray[Video]):
    __slots__ = ()

    def __init__(self, content=()):
        super().__init__((Video, FakeVideo), content, lambda video: video.filename)


class GroupField:
    __slots__ = ("field_value",)

    def __init__(self, field_value=None):
        self.field_value = field_value

    def is_defined(self):
        return self.field_value is not None

    @property
    def field(self):
        return self.field_value

    @property
    def length(self):
        return len(str(self.field_value))

    @property
    @abstractmethod
    def count(self):
        raise NotImplementedError()


class Group(GroupField):
    __slots__ = ("videos",)

    def __init__(self, field_value=None, videos: Sequence[Video] = ()):
        super().__init__(field_value)
        self.videos = VideoArray(videos)

    @property
    def count(self):
        return len(self.videos)


class GroupStat(GroupField):
    __slots__ = ("_count",)

    def __init__(self, field_value=None, count=0):
        super().__init__(field_value)
        self._count = count

    @property
    def count(self):
        return self._count


class GroupArray(LookupArray[Group]):
    __slots__ = "field", "is_property"

    def __init__(self, field: str, is_property: bool, content: Iterable[Group]):
        super().__init__(Group, content, lambda group: group.field_value)
        self.field = field
        self.is_property = is_property


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
        sorting: Optional[str] = FIELD,
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

    def sort(self, groups: Iterable[Group]) -> List[Group]:
        return sorted(
            groups,
            key=lambda group: (
                group.is_defined(),
                to_comparable(getattr(group, self.sorting), self.reverse),
                # Add group field value in any case.
                # If sorting is not field, then we will use group field
                # to sort groups with same sorting value
                to_comparable(group.field, self.reverse),
            ),
        )


class SearchDef(ToDict):
    __slots__ = "text", "cond"
    __print_none__ = True
    _Cond = Enumeration(("and", "or", "exact", "id"))

    def __init__(self, text: Optional[str] = None, cond: Optional[str] = None):
        self.text = text.strip() if text else None
        self.cond = self._Cond(cond.strip() if cond else "and")

    def __bool__(self):
        return bool(self.text)
