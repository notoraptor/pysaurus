import re

__regex_short__ = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")

from copy import deepcopy

from pysaurus.core.functions import is_attribute_name


class Type:
    """
    name: typedef = default
        name: string, required
        typedef: optional, attribute type (`type`) and short name (`str`). Either:
            type: attribute type (short name set to None)
            short: attribute short name (type set to default's type)
            (type, short) or (short, type): attribute type and short name
        default: optional
            If not provided:
                No default allowed: value required for this attribute.
                If type not provided, any type allowed.
            If None:
                None allowed as value.
                If type not provided, any type allowed.
            If provided:
                Will be validated against attribute type
                If type not provided, type is default's type
    NB: If one attribute has short name, then all attributes must have short names
    """

    __slots__ = (
        "name",
        "short",
        "type",
        "default",
        "to_dict",
        "from_dict",
        "allowed_types",
        "_get_default",
    )

    def __init__(self, name, typedef, *default):
        assert is_attribute_name(name)
        if typedef is None:
            short, ktype = None, None
        elif isinstance(typedef, (tuple, list)):
            v1, v2 = typedef
            if isinstance(v1, str):
                assert isinstance(v2, type)
                short, ktype = v1, v2
            else:
                assert isinstance(v1, type)
                assert isinstance(v2, str)
                short, ktype = v2, v1
        elif isinstance(typedef, str):
            short, ktype = typedef, None
        else:
            assert isinstance(typedef, type)
            short, ktype = None, typedef
        if default:
            (default_value,) = default
            if ktype is None and default_value is not None:
                ktype = type(default_value)
        if short is not None:
            assert __regex_short__.match(short)
        self.name = name
        self.short = short
        self.type = ktype
        self.default = default
        self.to_dict = self.standard_to_dict
        self.from_dict = self.standard_from_dict
        self.allowed_types = None
        self._get_default = None
        if self.type:
            self.allowed_types = (int, float) if self.type is float else (self.type,)
        if self.short is None:
            self.short = self.name

    def __str__(self):
        ret = self.name + (f"({self.short})" if self.short else "")
        ret += ": " + (self.type.__name__ if self.type else "Any")
        ret += f" = {self.default[0]}" if self.default else ""
        return ret

    def __call__(self, *args):
        if len(args) == 0:
            return None if self.accepts_none() else self.new()
        else:
            (value,) = args
            if value is None:
                if not self.accepts_none():
                    raise ValueError(f"None forbidden for attribute: {self.name}")
                return None
            else:
                return self.validate(value)

    def _get_immutable_default(self):
        return self.default[0]

    def _get_mutable_default(self):
        return deepcopy(self.default[0])

    def accepts_none(self):
        return self.default and self.default[0] is None

    def new(self):
        if not self.default:
            raise ValueError(f"No default value available for attribute: {self.name}")
        if self._get_default is None:
            self(self.default[0])
            if isinstance(self.default[0], (bool, int, float, str, bytes)):
                self._get_default = self._get_immutable_default
            else:
                self._get_default = self._get_mutable_default
        return self._get_default()

    def validate(self, value):
        if self.allowed_types and not isinstance(value, self.allowed_types):
            raise TypeError(
                f"{self.name}: type error, "
                f"expected {self.allowed_types}, got {type(value)}"
            )
        return value

    def standard_to_dict(self, obj, value):
        return self(value)

    def standard_from_dict(self, cls, value):
        return self(value)

    def to_linear(self):
        return [self.short, False]
