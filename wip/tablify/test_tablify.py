from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import pytest

from wip.tablify.core import (
    IncludeExcludeError,
    NoFieldAfterExcludingError,
    dicts_to_table,
    get_slots,
    objects_to_table,
)


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


@dataclass(slots=True)
class SomethingWithSlots:
    thing_id: int
    start: datetime
    end: datetime
    quantity: float

    @classmethod
    def init(cls, index: int) -> "SomethingWithSlots":
        start = datetime.now() + timedelta(days=index)
        end = start + timedelta(hours=index)
        quantity = index * 1.23
        return cls(thing_id=index, start=start, end=end, quantity=quantity)


class SomethingWithProps(SomethingWithSlots):
    __props__ = ("thing_id", "end")
    __slots__ = ()


MOCK_TIME = "2025-01-01 00:00:00"


def test_get_slots():
    assert list(get_slots(Something)) == []
    assert list(get_slots(SomethingWithSlots)) == [
        "thing_id",
        "start",
        "end",
        "quantity",
    ]


@pytest.mark.freeze_time(MOCK_TIME)
def test_tablify(file_regression):
    things = [Something(i) for i in range(15)]
    fields = ["thing_id", "start", "end"]
    file_regression.check(objects_to_table(things, fields))


@pytest.mark.freeze_time(MOCK_TIME)
def test_tablify_exclude(file_regression):
    things = [Something(i) for i in range(15)]
    file_regression.check(objects_to_table(things, exclude=["start"]))


@pytest.mark.freeze_time(MOCK_TIME)
def test_tablify_full(file_regression):
    things = [Something(i) for i in range(15)]
    file_regression.check(objects_to_table(things))


@pytest.mark.freeze_time(MOCK_TIME)
def test_tablify_full_with_slots(file_regression):
    things = [SomethingWithSlots.init(i) for i in range(15)]
    file_regression.check(objects_to_table(things))


@pytest.mark.freeze_time(MOCK_TIME)
def test_tablify_with_props(file_regression):
    things = [SomethingWithProps.init(i) for i in range(15)]
    file_regression.check(objects_to_table(things))


@pytest.mark.freeze_time(MOCK_TIME)
def test_tablify_dicts(file_regression):
    rename = {"thing_id": "dict_id"}
    things = [Something(i).to_dict(rename) for i in range(15)]
    fields = ["dict_id", "start", "quantity"]
    file_regression.check(dicts_to_table(things, fields))


@pytest.mark.freeze_time(MOCK_TIME)
def test_tablify_dicts_exclude(file_regression):
    rename = {"thing_id": "dict_id"}
    things = [Something(i).to_dict(rename) for i in range(15)]
    file_regression.check(dicts_to_table(things, exclude=["start"]))


@pytest.mark.freeze_time(MOCK_TIME)
def test_tablify_dicts_full(file_regression):
    rename = {"thing_id": "dict_id"}
    things = [Something(i).to_dict(rename) for i in range(15)]
    file_regression.check(dicts_to_table(things))


@pytest.mark.freeze_time(MOCK_TIME)
def test_tablify_include_exclude_error():
    things = [Something(i) for i in range(15)]
    with pytest.raises(IncludeExcludeError):
        objects_to_table(things, include=["thing_id"], exclude=["start"])

    with pytest.raises(NoFieldAfterExcludingError):
        objects_to_table(things, exclude=["start", "end", "quantity", "thing_id"])

    rename = {"thing_id": "dict_id"}
    dicts = [thing.to_dict(rename) for thing in things]
    with pytest.raises(IncludeExcludeError):
        dicts_to_table(dicts, include=["thing_id"], exclude=["start"])

    with pytest.raises(NoFieldAfterExcludingError):
        dicts_to_table(dicts, exclude=["start", "end", "quantity", "dict_id"])
