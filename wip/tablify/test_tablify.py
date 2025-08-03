from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import pytest

from wip.tablify.core import (
    IncludeExcludeError,
    NoFieldAfterExcludingError,
    dicts_to_table,
    objects_to_table,
)


class Exclude(Enum):
    NONE = "none"
    SOME = "some"
    ALL = "all"


class Empty:
    def __init__(self, index: int):
        pass


class EmptyWithProps(Empty):
    __props__ = ()


class EmptyWithSlots:
    __slots__ = ()

    def __init__(self, index: int):
        pass


class EmptyWithPropsAndSlots(EmptyWithSlots):
    __props__ = ()


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
    __slots__ = ("quantity", "thing_id", "start", "end")

    def __init__(self, index):
        self.thing_id = index
        self.start = datetime.now() + timedelta(days=index)
        self.end = self.start + timedelta(hours=index)
        self.quantity = index * 1.23


class SomethingWithPropsAndSlots(SomethingWithSlots):
    __props__ = ("thing_id", "end")


class AbstractCase:
    __fields__ = ("thing_id", "start", "end")
    __exclude__ = ("thing_id", "start", "unknown")
    __exclude_all__ = ("thing_id", "start", "end", "quantity")

    def __init__(
        self,
        factory: callable,
        function: callable,
        cls_name: str,
        fields: bool = False,
        exclude: Exclude = Exclude.NONE,
    ):
        names = []
        if fields:
            names.append("fields")
        if exclude != Exclude.NONE:
            names.append("exclude")
        names.append(cls_name)

        self.factory = factory
        self.fields = fields
        self.exclude = exclude
        self.function = function
        self.name = "_".join(names)

    def generate(self):
        kwargs = {}
        if self.fields:
            kwargs["include"] = self.__fields__
        if self.exclude != Exclude.NONE:
            kwargs["exclude"] = (
                self.__exclude__
                if self.exclude == Exclude.SOME
                else self.__exclude_all__
            )
        elements = [self.factory(i) for i in range(15)]
        return self.function(elements, **kwargs)

    def check(self):
        return self.generate()


class Case(AbstractCase):
    def __init__(
        self, cls: type, fields: bool = False, exclude: Exclude = Exclude.NONE
    ):
        super().__init__(
            factory=cls,
            function=objects_to_table,
            cls_name=cls.__name__,
            fields=fields,
            exclude=exclude,
        )


class Raise(Case):
    def __init__(
        self,
        cls: type,
        exception: type[Exception],
        fields: bool = False,
        exclude: Exclude = Exclude.NONE,
    ):
        super().__init__(cls, fields, exclude)
        self.name = f"{self.name}_raises_{exception.__name__}"
        self.exception = exception

    def check(self):
        with pytest.raises(self.exception):
            self.generate()
        return None


class DictCase(AbstractCase):
    __rename__ = {"thing_id": "dict_id"}
    __fields__ = ("dict_id", "start", "end")
    __exclude__ = ("dict_id", "start", "unknown")
    __exclude_all__ = ("dict_id", "start", "end", "quantity")

    @classmethod
    def _factory(cls, index: int) -> dict[str, Any]:
        return Something(index).to_dict(rename=cls.__rename__)

    def __init__(
        self,
        name: str = "DictSomething",
        fields: bool = False,
        exclude: Exclude = Exclude.NONE,
    ):
        super().__init__(
            self._factory, dicts_to_table, name, fields=fields, exclude=exclude
        )


class EmptyDictCase(DictCase):
    def __init__(
        self,
        name: str = "DictEmpty",
        fields: bool = False,
        exclude: Exclude = Exclude.NONE,
    ):
        super().__init__(name, fields, exclude)

    @classmethod
    def _factory(cls, index: int) -> dict[str, Any]:
        return {}


MOCK_TIME = "2025-01-01 00:00:00"


def test_mock_classes():
    assert not hasattr(Empty, "__props__")
    assert not hasattr(Empty, "__slots__")

    assert hasattr(EmptyWithProps, "__props__")
    assert not hasattr(EmptyWithProps, "__slots__")

    assert not hasattr(EmptyWithSlots, "__props__")
    assert hasattr(EmptyWithSlots, "__slots__")

    assert hasattr(EmptyWithPropsAndSlots, "__props__")
    assert hasattr(EmptyWithPropsAndSlots, "__slots__")

    assert not hasattr(Something, "__props__")
    assert not hasattr(Something, "__slots__")

    assert hasattr(SomethingWithProps, "__props__")
    assert not hasattr(SomethingWithProps, "__slots__")

    assert not hasattr(SomethingWithSlots, "__props__")
    assert hasattr(SomethingWithSlots, "__slots__")

    assert hasattr(SomethingWithPropsAndSlots, "__props__")
    assert hasattr(SomethingWithPropsAndSlots, "__slots__")


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
            Raise(Something, NoFieldAfterExcludingError, exclude=Exclude.ALL),
            Raise(Something, IncludeExcludeError, fields=True, exclude=Exclude.SOME),
            Case(Something),
            Case(SomethingWithSlots),
            Case(SomethingWithProps),
            Case(SomethingWithPropsAndSlots),
            Case(Something, exclude=Exclude.SOME),
            Case(SomethingWithSlots, exclude=Exclude.SOME),
            Case(SomethingWithProps, exclude=Exclude.SOME),
            Case(SomethingWithPropsAndSlots, exclude=Exclude.SOME),
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


@pytest.mark.freeze_time(MOCK_TIME)
@pytest.mark.parametrize(
    "case",
    [
        pytest.param(case, id=case.name)
        for case in [DictCase(), DictCase(exclude=Exclude.SOME), DictCase(fields=True)]
    ],
)
def test_tablify_dicts(case: Case, file_regression):
    table_string = case.check()
    if table_string:
        file_regression.check(table_string)


@pytest.mark.freeze_time(MOCK_TIME)
def test_tablify_dicts_errors():
    with pytest.raises(NoFieldAfterExcludingError):
        EmptyDictCase().check()

    with pytest.raises(NoFieldAfterExcludingError):
        DictCase(exclude=Exclude.ALL).check()

    with pytest.raises(IncludeExcludeError):
        DictCase(fields=True, exclude=Exclude.SOME).check()
