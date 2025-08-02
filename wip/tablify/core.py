import inspect
from abc import ABC
from collections.abc import Collection
from io import StringIO
from itertools import chain
from typing import Any, Iterable


def get_slots(cls: type) -> Iterable[str]:
    return chain.from_iterable(getattr(typ, "__slots__", ()) for typ in cls.__mro__)


class NoFieldAfterExcludingError(Exception):
    """Raised when no fields are left after excluding some fields."""


class IncludeExcludeError(Exception):
    """Raised when both include and exclude are specified."""


class AbstractProvider(ABC):
    def get_field(self, el: Any, field: str) -> Any:
        raise NotImplementedError()

    def get_fields(self, el: Any) -> list[str]:
        raise NotImplementedError()

    def get_fields_and_rows(
        self, elements: Iterable[Any], exclude: Collection[str] = ()
    ) -> tuple[list[str], list[list[str]]]:
        fields = []
        rows = []
        try:
            it = iter(elements)
            el = next(it)
            fields = self.get_fields(el)
            if exclude:
                fields = [field for field in fields if field not in exclude]
            if not fields:
                raise NoFieldAfterExcludingError()
            rows = []
            while True:
                rows.append([str(self.get_field(el, field)) for field in fields])
                el = next(it)
        except StopIteration:
            pass
        return fields, rows


class ObjectsProvider(AbstractProvider):
    def get_field(self, el: Any, field: str) -> Any:
        return getattr(el, field)

    def get_fields(self, el: Any) -> list[str]:
        cls = type(el)
        fields = list(getattr(cls, "__props__", ()))
        if not fields:
            fields = [field for field in get_slots(cls) if not field.startswith("_")]
        if not fields:
            fields = sorted(
                field
                for field in dir(el)
                if not field.startswith("_")
                and not inspect.ismethod(getattr(el, field))
            )
        return fields


class DictProvider(AbstractProvider):
    def get_field(self, el: dict[str, Any], field: str) -> Any:
        return el[field]

    def get_fields(self, el: dict[str, Any]) -> list[str]:
        return list(el.keys())


def objects_to_table(
    iterable: Iterable[Any],
    /,
    include: Collection[str] = (),
    *,
    exclude: Collection[str] = (),
    index: int | None = 1,
    indent: str = "",
    space: int = 2,
    provider: AbstractProvider | None = None,
) -> str:
    provider = provider or ObjectsProvider()

    fields = ()
    if include and exclude:
        raise IncludeExcludeError()
    elif include:
        fields = include

    if fields:
        if exclude:
            fields = [field for field in fields if field not in exclude]
        if not fields:
            raise NoFieldAfterExcludingError()
        rows = [
            [str(provider.get_field(el, field)) for field in fields] for el in iterable
        ]
    else:
        fields, rows = provider.get_fields_and_rows(iterable, exclude)

    headers = [f"[{field}]" for field in fields]

    if index is not None:
        headers = ["#"] + headers
        rows = [([str(index + i)] + row) for i, row in enumerate(rows)]

    table = [headers] + rows
    nb_cols = len(headers)
    col_sizes = [max([len(row[i]) for row in table]) + space for i in range(nb_cols)]

    with StringIO() as output:
        for row in table:
            print(
                indent + "".join(col.rjust(size) for size, col in zip(col_sizes, row)),
                file=output,
            )
        return output.getvalue()


def dicts_to_table(
    iterable: Iterable[dict[str, Any]],
    /,
    include: Collection[str] = (),
    *,
    exclude: Collection[str] = (),
    index: int | None = 1,
    indent: str = "",
    space: int = 2,
) -> str:
    return objects_to_table(
        iterable,
        include,
        exclude=exclude,
        index=index,
        indent=indent,
        space=space,
        provider=DictProvider(),
    )
