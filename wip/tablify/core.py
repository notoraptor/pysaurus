import inspect
from abc import ABC
from collections.abc import Collection
from io import StringIO
from itertools import chain
from typing import Any, Iterable


def get_slots(cls: type) -> Iterable[str]:
    """Get slots of a class, including from base classes."""
    return chain.from_iterable(getattr(typ, "__slots__", ()) for typ in cls.__mro__)


class NoFieldError(Exception):
    """Raised when a field is not found in the object."""


class NoFieldAfterExcludingError(Exception):
    """Raised when no fields are left after excluding some fields."""


class IncludeExcludeError(Exception):
    """Raised when both include and exclude are specified."""


class AbstractProvider(ABC):
    """Abstract class to get values and field names from an object or a dictionary."""

    def get_value(self, el: Any, field: str) -> Any:
        """Get value of a field from given element."""
        raise NotImplementedError()

    def get_fields(self, el: Any) -> list[str]:
        """Get field names from given element."""
        raise NotImplementedError()


class ObjectsProvider(AbstractProvider):
    """Provider for objects other than dictionaries."""

    def get_value(self, el: Any, field: str) -> Any:
        return getattr(el, field)

    def get_fields(self, el: Any) -> list[str]:
        """
        Get field names from an object.

        Methods looks for field names in the following order:
        1) looking for class attribute `__props__`
        2) looking for `__slots__` (including base classes)
        3) falling back to all public attributes that are not methods.
        """
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
    """Provider for dictionaries."""

    def get_value(self, el: dict[str, Any], field: str) -> Any:
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
    """
    Convert an iterable of objects or dictionaries into a formatted string table.
    :param iterable: Iterable of objects or dictionaries.
    :param include: List of fields to include in the table.
        If not specified, all fields will be included.
        Mutually exclusive with `exclude`.
    :param exclude: List of fields to exclude from the table.
        Mutually exclusive with `include`.
    :param index: If not None, adds an index column starting from this value.
    :param indent: String to prepend to each line of the table.
    :param space: Number of spaces to add between columns.
    :return: Formatted string table.
    :raises IncludeExcludeError: If both include and exclude are specified.
    :raises NoFieldError:
        If `include` is not specified and no fields can be determined
        from the first element.
    :raises NoFieldAfterExcludingError:
        If `exclude` is specified and no fields are left after excluding.
    """
    if include and exclude:
        raise IncludeExcludeError()

    fields = include
    rows = []
    iterator = iter(iterable)
    try:
        el = next(iterator)
        provider = DictProvider() if isinstance(el, dict) else ObjectsProvider()
        fields = fields or provider.get_fields(el)
        if not fields:
            raise NoFieldError()
        if exclude:
            if not isinstance(exclude, set):
                exclude = set(exclude)
            fields = [field for field in fields if field not in exclude]
        if not fields:
            raise NoFieldAfterExcludingError()

        while True:
            rows.append([str(provider.get_value(el, field)) for field in fields])
            el = next(iterator)
    except StopIteration:
        if not rows:
            return ""

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
