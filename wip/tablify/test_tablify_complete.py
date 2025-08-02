from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

import pytest

from wip.tablify.core import (
    IncludeExcludeError,
    NoFieldAfterExcludingError,
    objects_to_table,
)


class Empty:
    def __init__(self, index: int):
        pass


class EmptyWithProps:
    __props__ = ()

    def __init__(self, index: int):
        pass


class EmptyWithSlots:
    __slots__ = ()

    def __init__(self, index: int):
        pass


class EmptyWithPropsAndSlots:
    __props__ = ()
    __slots__ = ()

    def __init__(self, index: int):
        pass


class Something:
    def __init__(self, index):
        self.thing_id = index
        self.start = datetime.now() + timedelta(days=index)
        self.end = self.start + timedelta(hours=index)
        self.quantity = index * 1.23

    def to_dict(self, rename: dict[str, str] | None = None) -> dict[str, Any]:
        if rename is None:
            rename = {}
        return {
            rename.get(key, key): getattr(self, key)
            for key in ("thing_id", "quantity", "start", "end")
        }


class SomethingWithProps(Something):
    __props__ = ("thing_id", "end")


class SomethingWithSlots:
    __slots__ = ("thing_id", "start", "end", "quantity")

    def __init__(self, index):
        self.thing_id = index
        self.start = datetime.now() + timedelta(days=index)
        self.end = self.start + timedelta(hours=index)
        self.quantity = index * 1.23


class SomethingWithPropsAndSlots:
    __props__ = ("thing_id", "end")
    __slots__ = ("thing_id", "start", "end", "quantity")

    def __init__(self, index):
        self.thing_id = index
        self.start = datetime.now() + timedelta(days=index)
        self.end = self.start + timedelta(hours=index)
        self.quantity = index * 1.23


INCLUDE = ("thing_id", "start", "end")
EXCLUDE = ("thing_id", "start", "unknown")
EXCLUDE_ALL = ("thing_id", "start", "end", "quantity")


class Case:
    def __init__(self, cls: type, fields: bool = False, exclude: Sequence[str] = ()):
        # props = hasattr(cls, "__props__")
        # slots = hasattr(cls, "__slots__")

        names = []
        if fields:
            names.append("fields")
        if exclude:
            names.append("exclude")
        names.append(cls.__name__)

        self.cls = cls
        self.fields = fields
        self.exclude = exclude
        self.name = "_".join(names)

    def generate(self):
        kwargs = {}
        if self.fields:
            kwargs["include"] = INCLUDE
        if self.exclude:
            kwargs["exclude"] = self.exclude
        elements = [self.cls(i) for i in range(15)]
        return objects_to_table(elements, **kwargs)

    def check(self):
        return self.generate()


class Raise(Case):
    def __init__(
        self,
        cls: type,
        exception: type[Exception],
        fields: bool = False,
        exclude: Sequence[str] = (),
    ):
        super().__init__(cls, fields, exclude)
        self.name = f"{self.name}_raises_{exception.__name__}"
        self.exception = exception

    def check(self):
        with pytest.raises(self.exception):
            self.generate()
        return None


MOCK_TIME = "2025-01-01 00:00:00"


@pytest.mark.freeze_time(MOCK_TIME)
@pytest.mark.parametrize(
    "case",
    [
        pytest.param(case, id=case.name)
        for case in [
            Raise(Empty, NoFieldAfterExcludingError),
            Raise(EmptyWithProps, NoFieldAfterExcludingError),
            Raise(EmptyWithSlots, NoFieldAfterExcludingError),
            Raise(EmptyWithPropsAndSlots, NoFieldAfterExcludingError),
            Raise(Something, NoFieldAfterExcludingError, exclude=EXCLUDE_ALL),
            Raise(Empty, IncludeExcludeError, fields=True, exclude=EXCLUDE),
            Raise(Something, IncludeExcludeError, fields=True, exclude=EXCLUDE),
            Case(Something),
            Case(SomethingWithSlots),
            Case(SomethingWithProps),
            Case(SomethingWithPropsAndSlots),
            Case(Something, exclude=EXCLUDE),
            Case(SomethingWithSlots, exclude=EXCLUDE),
            Case(SomethingWithProps, exclude=EXCLUDE),
            Case(SomethingWithPropsAndSlots, exclude=EXCLUDE),
            Case(Something, fields=True),
            Case(SomethingWithSlots, fields=True),
            Case(SomethingWithProps, fields=True),
            Case(SomethingWithPropsAndSlots, fields=True),
        ]
    ],
)
def test_tablify(case: Case, file_regression):
    table_string = case.check()
    if table_string:
        file_regression.check(table_string)
