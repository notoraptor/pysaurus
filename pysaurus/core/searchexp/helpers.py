from __future__ import annotations

import types
import typing
from typing import get_type_hints

from .types import FieldType, SetType

# Standard Python types mapped automatically
_AUTO_MAP: dict[type, FieldType] = {
    bool: FieldType.BOOL,
    int: FieldType.INT,
    float: FieldType.FLOAT,
    str: FieldType.STR,
}


def fields_from_class(
    cls: type,
    *,
    type_mapping: dict[type, FieldType] | None = None,
    exclude: set[str] | None = None,
) -> dict[str, FieldType | SetType]:
    """Introspect a class's annotations and produce a {name: FieldType} dict.

    Parameters
    ----------
    cls
        An annotated class (e.g. VideoPattern).
    type_mapping
        Mapping from custom Python types to FieldType.
        Standard types (bool, int, float, str, list[str]) are mapped
        automatically.
    exclude
        Attribute names to exclude from the result.

    Raises
    ------
    TypeError
        If an annotated type cannot be resolved (not standard, not in
        type_mapping).
    """
    full_map = dict(_AUTO_MAP)
    if type_mapping:
        full_map.update(type_mapping)

    exclude_set = exclude or set()
    hints = _get_annotations(cls, full_map)
    result: dict[str, FieldType | SetType] = {}

    for name, annotation in hints.items():
        if name.startswith("_") or name in exclude_set:
            continue

        field_type = _resolve_annotation(annotation, full_map)
        if field_type is None:
            raise TypeError(
                f"Cannot resolve type for '{name}': {annotation!r}. "
                f"Add it to type_mapping or exclude it."
            )
        result[name] = field_type

    return result


def _get_annotations(cls: type, type_map: dict[type, FieldType]) -> dict[str, type]:
    """Get resolved type annotations from a class.

    Tries get_type_hints first; falls back to manual resolution of
    __annotations__ (needed when annotations reference types not in the
    module's global scope, e.g. types defined locally in tests).
    """
    try:
        return get_type_hints(cls)
    except Exception:
        pass

    # Fallback: collect raw annotations from MRO and resolve strings manually
    ns = _build_namespace(cls, type_map)
    result: dict[str, type] = {}
    for klass in reversed(cls.__mro__):
        raw = getattr(klass, "__annotations__", {})
        for name, ann in raw.items():
            if isinstance(ann, str):
                try:
                    ann = eval(ann, ns)  # noqa: S307
                except Exception:
                    pass
            result[name] = ann
    return result


def _build_namespace(cls: type, type_map: dict[type, FieldType]) -> dict[str, type]:
    """Build a namespace dict for evaluating annotation strings."""
    import builtins

    ns: dict[str, type] = {}
    ns.update(vars(builtins))
    # Add the module globals if available
    module = getattr(cls, "__module__", None)
    if module:
        import sys

        mod = sys.modules.get(module)
        if mod:
            ns.update(vars(mod))
    # Add all types from the type_map
    for t in type_map:
        if hasattr(t, "__name__"):
            ns[t.__name__] = t
    return ns


def _resolve_annotation(
    annotation: type, type_map: dict[type, FieldType]
) -> FieldType | SetType | None:
    """Resolve a type annotation to a FieldType or SetType."""
    # Direct match
    if annotation in type_map:
        return type_map[annotation]

    # Handle list[X] / List[X] → SetType(element_type)
    origin = typing.get_origin(annotation)
    if origin is list:
        args = typing.get_args(annotation)
        if args:
            elem = _resolve_annotation(args[0], type_map)
            if isinstance(elem, FieldType):
                return SetType(elem)
        return None

    # Handle X | None (Union types) — unwrap to X
    if origin is types.UnionType or origin is typing.Union:
        args = typing.get_args(annotation)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            return _resolve_annotation(non_none[0], type_map)

    return None
