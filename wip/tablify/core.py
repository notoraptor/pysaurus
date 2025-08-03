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


def tablify(
    iterable: Iterable[Any],
    /,
    include: Collection[str] = (),
    *,
    exclude: Collection[str] = (),
    index: int | None = 1,
    indent: str = "",
    space: int = 2,
) -> str:
    if include and exclude:
        raise IncludeExcludeError()

    fields = include
    rows = []
    iterator = iter(iterable)
    try:
        el = next(iterator)
        if isinstance(el, dict):
            provider = DictProvider()
        else:
            provider = ObjectsProvider()

        fields = fields or provider.get_fields(el)
        if exclude:
            fields = [field for field in fields if field not in exclude]
        if not fields:
            raise NoFieldAfterExcludingError()

        while True:
            rows.append([str(provider.get_field(el, field)) for field in fields])
            el = next(iterator)
    except StopIteration:
        pass

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
