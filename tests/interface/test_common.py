"""Tests for pysaurus.interface.common.common formatters."""

from pysaurus.dbview.view_tools import GroupDef
from pysaurus.interface.common.common import FIELD_MAP, pretty_grouping


def test_pretty_grouping_property_field_does_not_crash():
    # Regression: grouping by a custom property used to raise KeyError, because
    # pretty_grouping called FIELD_MAP.get_title() (attributes only) before
    # checking is_property. The property name is now used as its own title.
    text = pretty_grouping(GroupDef(field="my_prop", is_property=True))
    assert "my_prop" in text
    assert "property:" in text


def test_pretty_grouping_attribute_field_uses_field_map_title():
    # Attribute fields keep using their FIELD_MAP title (unchanged behavior).
    text = pretty_grouping(GroupDef(field="extension"))
    assert FIELD_MAP.get_title("extension") in text  # "file extension"
    assert "property:" not in text


def test_pretty_grouping_property_with_count_and_singletons():
    text = pretty_grouping(
        GroupDef(
            field="actors",
            is_property=True,
            sorting=GroupDef.COUNT,
            allow_singletons=True,
        )
    )
    assert "actors" in text
    assert "property:" in text
    assert text.startswith("many ")
    assert "#" in text
