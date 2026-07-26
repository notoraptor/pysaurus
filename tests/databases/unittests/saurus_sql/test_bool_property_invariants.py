"""A bool property is unique, and its domain is implied by the type.

The domain of a bool is exactly {False, True}, so allowing several values per
video would only ever mean "the whole domain", and spelling the domain out in
property_enumeration would restate the type. Both are therefore refused, at
every level: PropType (which also covers objects rebuilt from the database),
the collection methods that bypass it, and a SQL CHECK.

Old databases are brought in line by migration m0005, tested separately in
test_migration_m0005.py.
"""

import pytest

from pysaurus.application.exceptions import (
    BooleanPropertyCannotBeEnumerated,
    BooleanPropertyCannotBeMultiple,
    InvalidPropertyDefinition,
    InvalidPropertyValue,
)
from pysaurus.database.saurus.pysaurus_collection import PysaurusCollection
from pysaurus.properties.properties import PropType


@pytest.fixture
def db(mem_saurus_database) -> PysaurusCollection:
    return mem_saurus_database


class TestPropTypeRefusesInvalidBools:
    def test_init_refuses_multiple_bool(self):
        with pytest.raises(BooleanPropertyCannotBeMultiple):
            PropType("b", "bool", True, [False], None)

    def test_init_refuses_enumerated_bool(self):
        with pytest.raises(BooleanPropertyCannotBeEnumerated):
            PropType("b", "bool", False, [False], [False, True])

    def test_define_refuses_multiple_bool(self):
        with pytest.raises(BooleanPropertyCannotBeMultiple):
            PropType.define("b", "bool", False, True)

    def test_define_refuses_enumerated_bool(self):
        with pytest.raises(BooleanPropertyCannotBeEnumerated):
            PropType.define("b", "bool", [False, True], False)

    @pytest.mark.parametrize("definition", ["true", "", 1, 0, 1.0])
    def test_define_refuses_non_bool_default(self, definition):
        """Reading a bool out of text or numbers is the caller's job."""
        with pytest.raises(InvalidPropertyDefinition):
            PropType.define("b", "bool", definition, False)

    def test_define_accepts_plain_bool(self):
        prop = PropType.define("b", "bool", True, False)
        assert prop.type == "bool"
        assert prop.multiple is False
        assert prop.default == [True]
        assert prop.enumeration is None


class TestPossibleValues:
    def test_bool_domain_is_derived_not_stored(self):
        prop = PropType.define("b", "bool", False, False)
        assert prop.enumeration is None  # never stored
        assert prop.possible_values == [False, True]  # but always known

    def test_enumerated_property_reports_its_enumeration(self):
        prop = PropType.define("i", "int", [1, 2, 3], False)
        assert prop.possible_values == [1, 2, 3]

    def test_free_property_is_unconstrained(self):
        assert PropType.define("s", "str", "", True).possible_values is None


class TestExactTypeValidation:
    """bool is a subclass of int, so isinstance() is too lax here."""

    def test_int_property_refuses_bool_value(self):
        prop = PropType.define("i", "int", 0, False)
        with pytest.raises(InvalidPropertyValue):
            prop.validate(True)

    def test_float_property_refuses_bool_value(self):
        prop = PropType.define("f", "float", 0.0, False)
        with pytest.raises(InvalidPropertyValue):
            prop.validate(True)

    def test_multiple_int_property_refuses_bool_value(self):
        prop = PropType.define("i", "int", 0, True)
        with pytest.raises(InvalidPropertyValue):
            prop.validate([1, True])

    def test_float_property_still_promotes_int(self):
        prop = PropType.define("f", "float", 0.0, False)
        assert prop.validate(3) == 3.0

    def test_bool_property_refuses_int_value(self):
        prop = PropType.define("b", "bool", False, False)
        with pytest.raises(InvalidPropertyValue):
            prop.validate(1)


class TestDefineTypeChecksItsDefinition:
    """define() holds a definition to the same type rules as validate() holds
    values -- the int-to-float promotion included. Without this, a mistyped
    default slips into the property and validate() can then never equal it.
    """

    def test_int_property_refuses_bool_default(self):
        with pytest.raises(InvalidPropertyDefinition):
            PropType.define("i", "int", True, False)

    def test_float_property_refuses_bool_default(self):
        """float(True) is 1.0, but a bool is an answer, not a quantity."""
        with pytest.raises(InvalidPropertyDefinition):
            PropType.define("f", "float", True, False)

    def test_int_enumeration_refuses_bool_element(self):
        with pytest.raises(InvalidPropertyDefinition):
            PropType.define("i", "int", [1, True], False)

    def test_float_enumeration_refuses_bool_element(self):
        with pytest.raises(InvalidPropertyDefinition):
            PropType.define("f", "float", [1.5, True], False)

    @pytest.mark.parametrize("definition", ["3", 3.5])
    def test_int_property_refuses_non_int_default(self, definition):
        with pytest.raises(InvalidPropertyDefinition):
            PropType.define("i", "int", definition, False)

    def test_float_property_refuses_text_default(self):
        """Reading a float out of text is the caller's job, as for bool."""
        with pytest.raises(InvalidPropertyDefinition):
            PropType.define("f", "float", "3.5", False)

    def test_float_property_still_promotes_int_definition(self):
        prop = PropType.define("f", "float", 3, False)
        assert prop.default == [3.0]

    def test_float_enumeration_still_promotes_int_elements(self):
        prop = PropType.define("f", "float", [1, 2], False)
        assert prop.enumeration == [1.0, 2.0]
        assert prop.default == [1.0]


class TestDatabaseRefusesInvalidBools:
    def test_prop_type_add_refuses_multiple_bool(self, db):
        with pytest.raises(BooleanPropertyCannotBeMultiple):
            db.prop_type_add("flag", "bool", False, True)
        assert not db.get_prop_types(name="flag")

    def test_prop_type_set_multiple_refuses_bool(self, db):
        db.prop_type_add("flag", "bool", False, False)
        with pytest.raises(BooleanPropertyCannotBeMultiple):
            db.prop_type_set_multiple("flag", True)
        (prop,) = db.get_prop_types(name="flag")
        assert prop.multiple is False

    def test_sql_check_refuses_multiple_bool(self, db):
        """Last line of defence, for any path that bypasses Python."""
        db.prop_type_add("flag", "bool", False, False)
        with pytest.raises(Exception, match="CHECK constraint failed"):
            db.db.modify("UPDATE property SET multiple = 1 WHERE name = 'flag'")

    def test_bool_property_round_trips(self, db):
        db.prop_type_add("flag", "bool", False, False)
        (video_id,) = [v.video_id for v in db.get_videos(include=["video_id"])][:1]

        db.videos_tag_set("flag", {video_id: [True]})
        assert db.videos_tag_get("flag", indices=[video_id])[video_id] == [True]

        db.videos_tag_set("flag", {video_id: [False]})
        assert db.videos_tag_get("flag", indices=[video_id])[video_id] == [False]
