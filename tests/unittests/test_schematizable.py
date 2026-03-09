"""
Tests for pysaurus.core.json_type.Type and pysaurus.core.schematizable
(Schema, WithSchema, SchemaType, schema_prop).
"""

import pytest

from pysaurus.core.json_type import Type
from pysaurus.core.schematizable import (
    Schema,
    SchemaType,
    Short,
    WithSchema,
    schema_prop,
)


# ---------------------------------------------------------------------------
# Type — construction & typedef parsing
# ---------------------------------------------------------------------------


class TestTypeConstruction:
    def test_name_only_with_no_typedef(self):
        t = Type("age", None)
        assert t.name == "age"
        assert t.short == "age"  # short falls back to name
        assert t.type is None
        assert t.default == ()
        assert t.allowed_types is None

    def test_typedef_is_type(self):
        t = Type("age", int)
        assert t.type is int
        assert t.short == "age"
        assert t.allowed_types == (int,)

    def test_typedef_is_short_string(self):
        t = Type("age", "a")
        assert t.short == "a"
        assert t.type is None

    def test_typedef_tuple_short_then_type(self):
        t = Type("age", ("a", int))
        assert t.short == "a"
        assert t.type is int

    def test_typedef_tuple_type_then_short(self):
        t = Type("age", (int, "a"))
        assert t.short == "a"
        assert t.type is int

    def test_typedef_list_accepted(self):
        t = Type("age", ["a", int])
        assert t.short == "a"
        assert t.type is int

    def test_float_type_allows_int(self):
        t = Type("ratio", float)
        assert t.allowed_types == (int, float)

    def test_default_infers_type_when_typedef_is_short_only(self):
        t = Type("count", "c", 0)
        assert t.type is int
        assert t.short == "c"

    def test_default_none_no_type_inferred(self):
        t = Type("opt", "o", None)
        assert t.type is None

    def test_default_with_explicit_type(self):
        t = Type("name", ("n", str), "hello")
        assert t.type is str
        assert t.default == ("hello",)


# ---------------------------------------------------------------------------
# Type — __str__
# ---------------------------------------------------------------------------


class TestTypeStr:
    def test_str_no_default(self):
        t = Type("age", int)
        s = str(t)
        assert "age" in s
        assert "int" in s

    def test_str_with_default(self):
        t = Type("age", int, 42)
        s = str(t)
        assert "42" in s

    def test_str_any_type(self):
        t = Type("data", None)
        s = str(t)
        assert "Any" in s


# ---------------------------------------------------------------------------
# Type — __call__, validate, new, accepts_none
# ---------------------------------------------------------------------------


class TestTypeCall:
    def test_call_no_args_returns_default(self):
        t = Type("count", int, 5)
        assert t() == 5

    def test_call_no_args_accepts_none_returns_none(self):
        t = Type("opt", int, None)
        assert t() is None

    def test_call_no_args_no_default_raises(self):
        t = Type("required", int)
        with pytest.raises(ValueError, match="No default"):
            t()

    def test_call_with_value_validates(self):
        t = Type("age", int, 0)
        assert t(42) == 42

    def test_call_with_none_when_allowed(self):
        t = Type("opt", int, None)
        assert t(None) is None

    def test_call_with_none_when_forbidden(self):
        t = Type("age", int, 0)
        with pytest.raises(ValueError, match="None forbidden"):
            t(None)

    def test_validate_type_check(self):
        t = Type("age", int, 0)
        with pytest.raises(TypeError, match="type error"):
            t("not_an_int")

    def test_validate_float_accepts_int(self):
        t = Type("ratio", float, 0.0)
        assert t(3) == 3

    def test_validate_no_type_accepts_anything(self):
        t = Type("data", None, None)
        assert t("hello") == "hello"
        assert t(42) == 42
        assert t([1, 2]) == [1, 2]


# ---------------------------------------------------------------------------
# Type — new() and default behavior
# ---------------------------------------------------------------------------


class TestTypeNew:
    def test_new_immutable_default(self):
        t = Type("count", int, 5)
        assert t.new() == 5

    def test_new_string_default(self):
        t = Type("name", str, "")
        assert t.new() == ""

    def test_new_bool_default(self):
        t = Type("flag", bool, False)
        assert t.new() is False

    def test_new_mutable_default_returns_copy(self):
        t = Type("items", "i", [1, 2, 3])
        a = t.new()
        b = t.new()
        assert a == [1, 2, 3]
        assert a is not b  # deep copy

    def test_new_dict_default_returns_copy(self):
        t = Type("meta", "m", {"key": "val"})
        a = t.new()
        b = t.new()
        assert a == {"key": "val"}
        assert a is not b

    def test_new_no_default_raises(self):
        t = Type("required", int)
        with pytest.raises(ValueError, match="No default"):
            t.new()


# ---------------------------------------------------------------------------
# Type — to_dict / from_dict / to_linear
# ---------------------------------------------------------------------------


class TestTypeSerialization:
    def test_standard_to_dict(self):
        t = Type("age", int, 0)
        assert t.to_dict(None, 42) == 42

    def test_standard_from_dict(self):
        t = Type("age", int, 0)
        assert t.from_dict(int, 42) == 42

    def test_to_linear(self):
        t = Type("age", ("a", int), 0)
        assert t.to_linear() == ["a", False]

    def test_to_linear_no_explicit_short(self):
        t = Type("age", int, 0)
        assert t.to_linear() == ["age", False]


# ---------------------------------------------------------------------------
# Schema — construction & key mappings
# ---------------------------------------------------------------------------


class TestSchema:
    @pytest.fixture
    def schema(self):
        return Schema(
            [
                Type("name", ("n", str), ""),
                Type("age", ("a", int), 0),
                Type("active", ("x", bool), True),
            ]
        )

    def test_schema_contains_all_fields(self, schema):
        assert set(schema.schema.keys()) == {"name", "age", "active"}

    def test_from_short_mapping(self, schema):
        assert schema.from_short == {"n": "name", "a": "age", "x": "active"}

    def test_get_short_key(self, schema):
        assert schema.get_short_key("name") == "n"
        assert schema.get_short_key("age") == "a"

    def test_get_long_key(self, schema):
        assert schema.get_long_key("n") == "name"
        assert schema.get_long_key("a") == "age"

    def test_to_long_keys(self, schema):
        result = schema.to_long_keys({"n": "Alice", "a": 30})
        assert result == {"name": "Alice", "age": 30}

    def test_ensure_short_keys_passthrough(self, schema):
        d = {"n": "Alice"}
        assert schema.ensure_short_keys(d, keys_are_short=True) is d

    def test_ensure_short_keys_converts(self, schema):
        result = schema.ensure_short_keys({"name": "Alice"}, keys_are_short=False)
        assert result == {"n": "Alice"}

    def test_ensure_long_keys_passthrough(self, schema):
        d = {"name": "Alice"}
        assert schema.ensure_long_keys(d, keys_are_short=False) is d

    def test_ensure_long_keys_converts(self, schema):
        result = schema.ensure_long_keys({"n": "Alice"}, keys_are_short=True)
        assert result == {"name": "Alice"}


# ---------------------------------------------------------------------------
# Schema — get/set/has on short dicts
# ---------------------------------------------------------------------------


class TestSchemaShortDict:
    @pytest.fixture
    def schema(self):
        return Schema(
            [
                Type("name", ("n", str), ""),
                Type("age", ("a", int), 0),
                Type("opt", ("o", int), None),
            ]
        )

    def test_get_existing_key(self, schema):
        data = {"n": "Alice", "a": 30}
        assert schema.get_from_short_dict(data, "name") == "Alice"
        assert schema.get_from_short_dict(data, "age") == 30

    def test_get_missing_key_returns_default(self, schema):
        data = {}
        assert schema.get_from_short_dict(data, "name") == ""
        assert schema.get_from_short_dict(data, "age") == 0

    def test_get_missing_nullable_returns_none(self, schema):
        data = {}
        assert schema.get_from_short_dict(data, "opt") is None

    def test_set_new_key(self, schema):
        data = {}
        modified = schema.set_into_short_dict(data, "name", "Bob")
        assert modified is True
        assert data == {"n": "Bob"}

    def test_set_same_value_not_modified(self, schema):
        data = {"n": "Alice"}
        modified = schema.set_into_short_dict(data, "name", "Alice")
        assert modified is False

    def test_set_different_value_modified(self, schema):
        data = {"n": "Alice"}
        modified = schema.set_into_short_dict(data, "name", "Bob")
        assert modified is True
        assert data["n"] == "Bob"

    def test_has_present(self, schema):
        data = {"n": "Alice"}
        assert schema.has_in_short_dict(data, "name") is True

    def test_has_absent(self, schema):
        data = {}
        assert schema.has_in_short_dict(data, "name") is False


# ---------------------------------------------------------------------------
# Schema — linear format (compact list representation)
# ---------------------------------------------------------------------------


class TestSchemaLinear:
    @pytest.fixture
    def schema(self):
        return Schema([Type("age", ("a", int), 0), Type("name", ("n", str), "")])

    def test_to_linear_type(self, schema):
        lt = schema.to_linear_type()
        # Sorted by name: age, name
        assert lt == [["a", False], ["n", False]]

    def test_short_dict_to_linear(self, schema):
        data = {"a": 25, "n": "Alice"}
        linear = Schema.short_dict_to_linear(data, schema.linear_type)
        assert linear == [25, "Alice"]

    def test_short_dict_to_linear_missing_keys(self, schema):
        data = {"a": 25}
        linear = Schema.short_dict_to_linear(data, schema.linear_type)
        assert linear == [25, None]

    def test_linear_to_short_dict(self, schema):
        linear = [25, "Alice"]
        result = Schema.linear_to_short_dict(schema.linear_type, linear)
        assert result == {"a": 25, "n": "Alice"}

    def test_linear_to_short_dict_skips_none(self, schema):
        linear = [25, None]
        result = Schema.linear_to_short_dict(schema.linear_type, linear)
        assert result == {"a": 25}

    def test_roundtrip_linear(self, schema):
        data = {"a": 42, "n": "Bob"}
        linear = Schema.short_dict_to_linear(data, schema.linear_type)
        back = Schema.linear_to_short_dict(schema.linear_type, linear)
        assert back == data


# ---------------------------------------------------------------------------
# WithSchema — basic operations
# ---------------------------------------------------------------------------


class TestWithSchema:
    @pytest.fixture
    def person_class(self):
        class Person(WithSchema):
            __slots__ = ()
            SCHEMA = Schema(
                [
                    Type("name", ("n", str), ""),
                    Type("age", ("a", int), 0),
                    Type("email", ("e", str), None),
                ]
            )

            name = schema_prop("name")
            age = schema_prop("age")
            email = schema_prop("email")

        return Person

    def test_init_empty(self, person_class):
        p = person_class()
        assert p.name == ""
        assert p.age == 0
        assert p.email is None

    def test_init_with_short_dict(self, person_class):
        p = person_class(short_dict={"n": "Alice", "a": 30})
        assert p.name == "Alice"
        assert p.age == 30

    def test_from_dict(self, person_class):
        p = person_class.from_dict({"n": "Bob", "a": 25})
        assert p.name == "Bob"
        assert p.age == 25

    def test_to_dict(self, person_class):
        p = person_class(short_dict={"n": "Alice", "a": 30})
        assert p.to_dict() == {"n": "Alice", "a": 30}

    def test_from_keys(self, person_class):
        p = person_class.from_keys(name="Charlie", age=40)
        assert p.name == "Charlie"
        assert p.age == 40
        assert p.to_dict() == {"n": "Charlie", "a": 40}

    def test_str(self, person_class):
        p = person_class(short_dict={"n": "Alice"})
        s = str(p)
        assert "Person" in s
        assert "'n': 'Alice'" in s

    def test_set_via_schema_prop(self, person_class):
        p = person_class()
        p.name = "Diana"
        assert p.name == "Diana"
        assert p.to_dict() == {"n": "Diana"}

    def test_set_returns_modified_flag(self, person_class):
        p = person_class()
        assert p._set("name", "Alice") is True
        assert p._set("name", "Alice") is False  # same value
        assert p._set("name", "Bob") is True

    def test_has(self, person_class):
        p = person_class()
        assert p._has("name") is False
        p.name = "Alice"
        assert p._has("name") is True

    def test_to_linear(self, person_class):
        p = person_class(short_dict={"n": "Alice", "a": 30})
        linear = p._to_linear()
        # Sorted by name: age, email, name
        assert linear == [30, None, "Alice"]

    def test_from_linear(self, person_class):
        p = person_class._from_linear([25, None, "Bob"])
        assert p.age == 25
        assert p.email is None
        assert p.name == "Bob"

    def test_roundtrip_linear(self, person_class):
        original = person_class(short_dict={"n": "Alice", "a": 30, "e": "a@b.c"})
        linear = original._to_linear()
        restored = person_class._from_linear(linear)
        assert restored.to_dict() == original.to_dict()


# ---------------------------------------------------------------------------
# WithSchema — from_keys with extra kwargs
# ---------------------------------------------------------------------------


class TestFromKeysExtraKwargs:
    def test_from_keys_passes_non_schema_kwargs(self):
        class Tagged(WithSchema):
            __slots__ = ("tag",)
            SCHEMA = Schema([Type("name", ("n", str), "")])

            def __init__(self, short_dict=None, tag=None):
                super().__init__(short_dict)
                self.tag = tag

        obj = Tagged.from_keys(name="Alice", tag="important")
        assert obj._get("name") == "Alice"
        assert obj.tag == "important"


# ---------------------------------------------------------------------------
# SchemaType — nested schemas
# ---------------------------------------------------------------------------


class TestSchemaType:
    @pytest.fixture
    def classes(self):
        class Inner(WithSchema):
            __slots__ = ()
            SCHEMA = Schema([Type("x", ("X", int), 0), Type("y", ("Y", int), 0)])

            x = schema_prop("x")
            y = schema_prop("y")

        class Outer(WithSchema):
            __slots__ = ()
            SCHEMA = Schema(
                [Type("label", ("l", str), ""), SchemaType("inner", ("i", Inner), {})]
            )

            label = schema_prop("label")
            inner = schema_prop("inner")

        return Inner, Outer

    def test_nested_from_dict(self, classes):
        Inner, Outer = classes
        outer = Outer.from_dict({"l": "test", "i": {"X": 10, "Y": 20}})
        assert outer.label == "test"
        assert isinstance(outer.inner, Inner)
        assert outer.inner.x == 10
        assert outer.inner.y == 20

    def test_nested_from_dict_empty_inner(self, classes):
        Inner, Outer = classes
        outer = Outer.from_dict({"l": "test", "i": {}})
        assert outer.inner.x == 0
        assert outer.inner.y == 0

    def test_nested_to_dict(self, classes):
        Inner, Outer = classes
        inner = Inner.from_dict({"X": 5, "Y": 15})
        outer = Outer(short_dict={"l": "hello"})
        outer.inner = inner
        d = outer.to_dict()
        assert d["l"] == "hello"
        # inner is stored as the Inner object; to_dict returns raw _d
        # SchemaType.standard_to_dict handles serialization
        schema_type = Outer.SCHEMA.schema["inner"]
        serialized = schema_type.to_dict(None, inner)
        assert serialized == {"X": 5, "Y": 15}

    def test_nested_to_dict_none_when_nullable(self):
        class Inner(WithSchema):
            __slots__ = ()
            SCHEMA = Schema([Type("x", ("X", int), 0)])

        class Outer(WithSchema):
            __slots__ = ()
            SCHEMA = Schema([SchemaType("inner", ("i", Inner), None)])

        schema_type = Outer.SCHEMA.schema["inner"]
        assert schema_type.to_dict(None, None) is None

    def test_nested_from_dict_none_when_nullable(self):
        class Inner(WithSchema):
            __slots__ = ()
            SCHEMA = Schema([Type("x", ("X", int), 0)])

        class Outer(WithSchema):
            __slots__ = ()
            SCHEMA = Schema([SchemaType("inner", ("i", Inner), None)])

        schema_type = Outer.SCHEMA.schema["inner"]
        assert schema_type.from_dict(None, None) is None

    def test_nested_to_dict_none_when_not_nullable_raises(self, classes):
        _, Outer = classes
        schema_type = Outer.SCHEMA.schema["inner"]
        with pytest.raises(ValueError, match="None forbidden"):
            schema_type.to_dict(None, None)

    def test_schema_type_validate_dict_input(self, classes):
        Inner, Outer = classes
        schema_type = Outer.SCHEMA.schema["inner"]
        result = schema_type.validate({"X": 3, "Y": 7})
        assert isinstance(result, Inner)
        assert result.x == 3
        assert result.y == 7

    def test_schema_type_validate_object_passthrough(self, classes):
        Inner, Outer = classes
        inner = Inner.from_dict({"X": 1, "Y": 2})
        schema_type = Outer.SCHEMA.schema["inner"]
        result = schema_type.validate(inner)
        assert result is inner

    def test_schema_type_new(self, classes):
        Inner, Outer = classes
        schema_type = Outer.SCHEMA.schema["inner"]
        result = schema_type.new()
        assert isinstance(result, Inner)

    def test_schema_type_to_linear(self, classes):
        Inner, Outer = classes
        schema_type = Outer.SCHEMA.schema["inner"]
        linear = schema_type.to_linear()
        assert linear[0] == "i"
        # Second element is Inner's linear type (sorted by name: x, y)
        assert linear[1] == [["X", False], ["Y", False]]

    def test_schema_type_no_explicit_type_defaults_to_with_schema(self):
        # When typedef has no type info, SchemaType defaults type to WithSchema
        st = SchemaType("data", ("d", WithSchema), {})
        assert st.type is WithSchema

    def test_schema_type_none_typedef_defaults_to_with_schema(self):
        st = SchemaType("data", None)
        assert st.type is WithSchema


# ---------------------------------------------------------------------------
# SchemaType — nested linear roundtrip
# ---------------------------------------------------------------------------


class TestNestedLinear:
    def test_roundtrip(self):
        class Inner(WithSchema):
            __slots__ = ()
            SCHEMA = Schema([Type("a", ("A", int), 0), Type("b", ("B", str), "")])

        class Outer(WithSchema):
            __slots__ = ()
            SCHEMA = Schema(
                [Type("name", ("n", str), ""), SchemaType("child", ("c", Inner), {})]
            )

        data = {"n": "test", "c": {"A": 42, "B": "hello"}}
        linear = Schema.short_dict_to_linear(data, Outer.SCHEMA.linear_type)
        # linear_type sorted by name: child, name
        # child has nested desc, name has False
        back = Schema.linear_to_short_dict(Outer.SCHEMA.linear_type, linear)
        assert back == data


# ---------------------------------------------------------------------------
# schema_prop descriptor
# ---------------------------------------------------------------------------


class TestSchemaProp:
    def test_getter_and_setter(self):
        class Item(WithSchema):
            __slots__ = ()
            SCHEMA = Schema([Type("value", ("v", int), 0)])
            value = schema_prop("value")

        item = Item()
        assert item.value == 0
        item.value = 42
        assert item.value == 42

    def test_setter_modifies_internal_dict(self):
        class Item(WithSchema):
            __slots__ = ()
            SCHEMA = Schema([Type("value", ("v", int), 0)])
            value = schema_prop("value")

        item = Item()
        item.value = 99
        assert item.to_dict() == {"v": 99}


# ---------------------------------------------------------------------------
# Real-world schemas: VIDEO_RUNTIME_INFO_SCHEMA
# ---------------------------------------------------------------------------


class TestRealWorldSchemas:
    def test_lazy_video_runtime_info(self):
        from pysaurus.video.lazy_video_runtime_info import LazyVideoRuntimeInfo

        info = LazyVideoRuntimeInfo()
        assert info.size == 0
        assert info.mtime == 0.0
        assert info.driver_id is None
        assert info.is_file is False

    def test_lazy_video_runtime_info_from_dict(self):
        from pysaurus.video.lazy_video_runtime_info import LazyVideoRuntimeInfo

        info = LazyVideoRuntimeInfo.from_dict(
            {"s": 1024, "m": 1234.5, "d": 7, "f": True}
        )
        assert info.size == 1024
        assert info.mtime == 1234.5
        assert info.driver_id == 7
        assert info.is_file is True

    def test_lazy_video_runtime_info_roundtrip(self):
        from pysaurus.video.lazy_video_runtime_info import LazyVideoRuntimeInfo

        data = {"s": 512, "m": 99.9, "d": 3, "f": True}
        info = LazyVideoRuntimeInfo.from_dict(data)
        assert info.to_dict() == data

    def test_video_schema_linear_type(self):
        from pysaurus.database.jsdb.jsdbvideo.lazy_video import LazyVideo

        lt = LazyVideo.SCHEMA.to_linear_type()
        # Should be a list of [short, desc] pairs, sorted by field name
        assert isinstance(lt, list)
        assert len(lt) == 32  # 32 fields in LazyVideo schema
        # runtime is a nested SchemaType with desc != False
        runtime_entry = next(p for p in lt if p[0] == "R")
        assert runtime_entry[1] != False  # nested type descriptor

    def test_video_schema_short_keys(self):
        from pysaurus.database.jsdb.jsdbvideo.lazy_video import LazyVideo

        assert LazyVideo.SCHEMA.get_short_key("filename") == "f"
        assert LazyVideo.SCHEMA.get_short_key("audio_codec") == "a"
        assert LazyVideo.SCHEMA.get_short_key("width") == "w"
        assert LazyVideo.SCHEMA.get_long_key("f") == "filename"
        assert LazyVideo.SCHEMA.get_long_key("a") == "audio_codec"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_type_short_falls_back_to_name(self):
        t = Type("long_name", int, 0)
        assert t.short == "long_name"

    def test_schema_no_fields(self):
        s = Schema(())
        assert s.schema == {}
        assert s.from_short == {}
        assert s.to_linear_type() == []

    def test_with_schema_empty(self):
        obj = WithSchema()
        assert obj.to_dict() == {}
        assert str(obj) == "WithSchema({})"

    def test_with_schema_from_dict_preserves_extra_keys(self):
        obj = WithSchema.from_dict({"unknown": 123})
        assert obj.to_dict() == {"unknown": 123}

    def test_type_mutable_default_independence(self):
        t = Type("items", "i", [])
        a = t.new()
        a.append(1)
        b = t.new()
        assert b == []  # not affected by mutation of a

    def test_schema_set_into_empty_dict_returns_true(self):
        s = Schema([Type("x", ("X", int), 0)])
        data = {}
        assert s.set_into_short_dict(data, "x", 0) is True
        # Now it's present, setting same value returns False
        assert s.set_into_short_dict(data, "x", 0) is False


# ---------------------------------------------------------------------------
# Short annotation — construction & validation
# ---------------------------------------------------------------------------


class TestShort:
    def test_basic(self):
        ann = Short["n", str]
        assert ann.short == "n"
        assert ann.type is str

    def test_with_int(self):
        ann = Short["a", int]
        assert ann.short == "a"
        assert ann.type is int

    def test_with_default(self):
        ann = Short["n", str, "hello"]
        assert ann.short == "n"
        assert ann.type is str
        assert ann.default == "hello"

    def test_with_none_default(self):
        from pysaurus.core.schematizable import _MISSING

        ann = Short["n", int, None]
        assert ann.default is None
        # Verify 2-param has no default
        ann2 = Short["n", int]
        assert ann2.default is _MISSING

    def test_wrong_param_count_raises(self):
        with pytest.raises(TypeError, match="2 or 3 parameters"):
            Short["only_one"]

    def test_non_string_short_raises(self):
        with pytest.raises(TypeError, match="must be a string"):
            Short[42, str]


# ---------------------------------------------------------------------------
# Annotation-based schema — __init_subclass__
# ---------------------------------------------------------------------------


class TestAnnotationSchema:
    def test_basic_fields_with_short(self):
        class Item(WithSchema):
            __slots__ = ()
            name: Short["n", str] = ""
            age: Short["a", int] = 0

        item = Item()
        assert item.name == ""
        assert item.age == 0
        item.name = "Alice"
        item.age = 30
        assert item.name == "Alice"
        assert item.age == 30
        assert item.to_dict() == {"n": "Alice", "a": 30}

    def test_fields_without_short(self):
        class Item(WithSchema):
            __slots__ = ()
            name: str = ""
            count: int = 0

        item = Item()
        assert item.name == ""
        item.name = "test"
        assert item.to_dict() == {"name": "test"}
        assert Item.SCHEMA.get_short_key("name") == "name"

    def test_required_field(self):
        class Item(WithSchema):
            __slots__ = ()
            name: Short["n", str]
            age: Short["a", int] = 0

        # Required field: no default, calling Type() raises
        with pytest.raises(ValueError, match="No default"):
            Item().name

    def test_nullable_field(self):
        class Item(WithSchema):
            __slots__ = ()
            opt: Short["o", int] = None

        item = Item()
        assert item.opt is None
        item.opt = 42
        assert item.opt == 42

    def test_from_dict(self):
        class Item(WithSchema):
            __slots__ = ()
            name: Short["n", str] = ""
            age: Short["a", int] = 0

        item = Item.from_dict({"n": "Bob", "a": 25})
        assert item.name == "Bob"
        assert item.age == 25

    def test_from_keys(self):
        class Item(WithSchema):
            __slots__ = ()
            name: Short["n", str] = ""
            age: Short["a", int] = 0

        item = Item.from_keys(name="Charlie", age=40)
        assert item.name == "Charlie"
        assert item.age == 40

    def test_linear_roundtrip(self):
        class Item(WithSchema):
            __slots__ = ()
            age: Short["a", int] = 0
            name: Short["n", str] = ""

        item = Item.from_dict({"a": 30, "n": "Alice"})
        linear = item._to_linear()
        restored = Item._from_linear(linear)
        assert restored.to_dict() == item.to_dict()

    def test_mutable_default(self):
        class Item(WithSchema):
            __slots__ = ()
            tags: Short["t", list] = []

        a = Item()
        b = Item()
        tags_a = a.tags
        tags_a.append("x")
        assert b.tags == []  # independent copy

    def test_bool_field(self):
        class Item(WithSchema):
            __slots__ = ()
            active: Short["x", bool] = False

        item = Item()
        assert item.active is False
        item.active = True
        assert item.active is True

    def test_float_accepts_int(self):
        class Item(WithSchema):
            __slots__ = ()
            ratio: Short["r", float] = 0.0

        item = Item()
        item.ratio = 3
        assert item.ratio == 3

    def test_type_validation(self):
        class Item(WithSchema):
            __slots__ = ()
            age: Short["a", int] = 0

        item = Item()
        with pytest.raises(TypeError, match="type error"):
            Item.SCHEMA.schema["age"].validate("not_int")

    def test_private_annotations_skipped(self):
        class Item(WithSchema):
            __slots__ = ()
            _internal: int
            name: Short["n", str] = ""

        assert "_internal" not in Item.SCHEMA.schema
        assert "name" in Item.SCHEMA.schema

    def test_explicit_schema_takes_precedence(self):
        class Item(WithSchema):
            __slots__ = ()
            SCHEMA = Schema([Type("x", ("X", int), 0)])
            x = schema_prop("x")
            name: str = ""  # annotation present but SCHEMA is explicit

        # SCHEMA should be the explicit one, not auto-built
        assert "x" in Item.SCHEMA.schema
        assert "name" not in Item.SCHEMA.schema

    def test_default_in_annotation_with_custom_property(self):
        class Item(WithSchema):
            __slots__ = ()
            name: Short["n", str, "default_name"]

            @property
            def name(self):
                return self._get("name").upper()

        # Default comes from annotation, not from class attribute
        item = Item()
        assert item.name == "DEFAULT_NAME"  # custom property applies
        assert Item.SCHEMA.schema["name"].default == ("default_name",)

    def test_custom_property_not_overwritten(self):
        class Item(WithSchema):
            __slots__ = ()
            value: Short["v", int, 0]

            @property
            def value(self):
                return self._get("value") * 2

        item = Item.from_dict({"v": 5})
        assert item.value == 10  # custom property, not schema_prop

    def test_custom_property_with_setter(self):
        class Item(WithSchema):
            __slots__ = ()
            count: Short["c", int, 0]

            @property
            def count(self):
                return self._get("count")

            @count.setter
            def count(self, v):
                self._set("count", max(0, v))

        item = Item()
        item.count = -5
        assert item.count == 0  # setter clamps to 0

    def test_mix_annotated_defaults_and_custom_properties(self):
        class Item(WithSchema):
            __slots__ = ()
            label: Short["l", str] = ""
            score: Short["s", int, 0]

            @property
            def score(self):
                return self._get("score") + 100

        item = Item.from_dict({"l": "test", "s": 5})
        assert item.label == "test"  # schema_prop (no custom property)
        assert item.score == 105  # custom property preserved

        # label has schema_prop setter, score doesn't
        item.label = "new"
        assert item.to_dict() == {"l": "new", "s": 5}

    def test_annotation_default_for_missing_key(self):
        class Item(WithSchema):
            __slots__ = ()
            data: Short["d", str, "fallback"]

            @property
            def data(self):
                return self._get("data")

        # Key missing from dict: default "fallback" used
        item = Item.from_dict({})
        assert item.data == "fallback"

    def test_two_param_short_with_custom_property_is_required(self):
        """Short with 2 params + custom property = required field (no default)."""

        class Item(WithSchema):
            __slots__ = ()
            name: Short["n", str]

            @property
            def name(self):
                return self._get("name")

        # Default is not set — property descriptor must not be used as default
        t = Item.SCHEMA.schema["name"]
        assert t.default == ()  # no default (required)
        with pytest.raises(ValueError, match="No default"):
            t.new()


# ---------------------------------------------------------------------------
# __schema_readonly__ — auto-generated readonly properties
# ---------------------------------------------------------------------------


class TestSchemaReadonly:
    def test_readonly_generates_getter_only(self):
        class Item(WithSchema):
            __slots__ = ()
            __schema_readonly__ = True
            name: Short["n", str] = ""
            age: Short["a", int] = 0

        item = Item.from_dict({"n": "Alice", "a": 30})
        assert item.name == "Alice"
        assert item.age == 30
        with pytest.raises(AttributeError):
            item.name = "Bob"

    def test_readwrite_default(self):
        class Item(WithSchema):
            __slots__ = ()
            name: Short["n", str] = ""

        item = Item()
        item.name = "Alice"
        assert item.name == "Alice"

    def test_readonly_custom_property_preserved(self):
        class Item(WithSchema):
            __slots__ = ()
            __schema_readonly__ = True
            raw: Short["r", int, 0]
            auto: Short["a", int] = 0

            @property
            def raw(self):
                return self._get("raw") * 10

        item = Item.from_dict({"r": 5, "a": 3})
        assert item.raw == 50  # custom property preserved
        assert item.auto == 3  # auto-generated readonly
        with pytest.raises(AttributeError):
            item.auto = 99

    def test_readonly_schema_still_correct(self):
        class Item(WithSchema):
            __slots__ = ()
            __schema_readonly__ = True
            x: Short["X", int] = 0
            y: Short["Y", str] = ""

        assert Item.SCHEMA.get_short_key("x") == "X"
        assert Item.SCHEMA.get_short_key("y") == "Y"
        item = Item.from_dict({})
        assert item.x == 0
        assert item.y == ""


# ---------------------------------------------------------------------------
# Annotation-based schema — nested WithSchema (auto SchemaType)
# ---------------------------------------------------------------------------


class TestAnnotationNestedSchema:
    def test_nested_auto_schema_type(self):
        class Inner(WithSchema):
            __slots__ = ()
            x: Short["X", int] = 0
            y: Short["Y", int] = 0

        class Outer(WithSchema):
            __slots__ = ()
            label: Short["l", str] = ""
            inner: Short["i", Inner] = {}

        # inner field should be a SchemaType
        inner_type = Outer.SCHEMA.schema["inner"]
        assert isinstance(inner_type, SchemaType)

        outer = Outer.from_dict({"l": "test", "i": {"X": 10, "Y": 20}})
        assert outer.label == "test"
        assert isinstance(outer.inner, Inner)
        assert outer.inner.x == 10
        assert outer.inner.y == 20

    def test_nested_to_dict(self):
        class Inner(WithSchema):
            __slots__ = ()
            val: Short["v", int] = 0

        class Outer(WithSchema):
            __slots__ = ()
            child: Short["c", Inner] = {}

        inner = Inner.from_dict({"v": 42})
        outer = Outer()
        outer.child = inner
        schema_type = Outer.SCHEMA.schema["child"]
        assert schema_type.to_dict(None, inner) == {"v": 42}

    def test_nested_linear_roundtrip(self):
        class Inner(WithSchema):
            __slots__ = ()
            a: Short["A", int] = 0

        class Outer(WithSchema):
            __slots__ = ()
            name: Short["n", str] = ""
            child: Short["c", Inner] = {}

        data = {"n": "test", "c": {"A": 42}}
        linear = Schema.short_dict_to_linear(data, Outer.SCHEMA.linear_type)
        back = Schema.linear_to_short_dict(Outer.SCHEMA.linear_type, linear)
        assert back == data


# ---------------------------------------------------------------------------
# Annotation vs old-style equivalence
# ---------------------------------------------------------------------------


class TestAnnotationEquivalence:
    def test_equivalent_to_manual_schema(self):
        """Annotation-based class produces the same SCHEMA as manual definition."""

        class ManualItem(WithSchema):
            __slots__ = ()
            SCHEMA = Schema(
                [
                    Type("name", ("n", str), ""),
                    Type("age", ("a", int), 0),
                    Type("active", ("x", bool), True),
                ]
            )
            name = schema_prop("name")
            age = schema_prop("age")
            active = schema_prop("active")

        class AnnotItem(WithSchema):
            __slots__ = ()
            name: Short["n", str] = ""
            age: Short["a", int] = 0
            active: Short["x", bool] = True

        # Same schema structure
        assert set(ManualItem.SCHEMA.schema.keys()) == set(
            AnnotItem.SCHEMA.schema.keys()
        )
        assert ManualItem.SCHEMA.from_short == AnnotItem.SCHEMA.from_short
        assert ManualItem.SCHEMA.linear_type == AnnotItem.SCHEMA.linear_type

        # Same behavior
        data = {"n": "Alice", "a": 30, "x": False}
        m = ManualItem.from_dict(dict(data))
        a = AnnotItem.from_dict(dict(data))
        assert m.name == a.name
        assert m.age == a.age
        assert m.active == a.active
        assert m.to_dict() == a.to_dict()
        assert m._to_linear() == a._to_linear()

    def test_equivalent_runtime_info(self):
        """Annotation equivalent of LazyVideoRuntimeInfo matches original."""
        from pysaurus.video.lazy_video_runtime_info import LazyVideoRuntimeInfo

        class AnnotRuntimeInfo(WithSchema):
            __slots__ = ()
            size: Short["s", int] = 0
            mtime: Short["m", float] = 0.0
            driver_id: Short["d", int] = None
            is_file: Short["f", bool] = False

        # Same schema mappings
        orig = LazyVideoRuntimeInfo.SCHEMA
        annot = AnnotRuntimeInfo.SCHEMA
        assert orig.from_short == annot.from_short
        assert orig.linear_type == annot.linear_type

        # Same behavior with data
        data = {"s": 1024, "m": 99.5, "d": 7, "f": True}
        o = LazyVideoRuntimeInfo.from_dict(dict(data))
        a = AnnotRuntimeInfo.from_dict(dict(data))
        assert o.size == a.size
        assert o.mtime == a.mtime
        assert o.driver_id == a.driver_id
        assert o.is_file == a.is_file
