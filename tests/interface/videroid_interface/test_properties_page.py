"""Coverage for the Properties page: action menu, rename/convert/delete, dialogs
and the create form (all branches)."""

import pytest

from pysaurus.interface.videroid.dialogs.move_values_dialog import MoveValuesDialog
from tests.interface.videroid_interface._widget_tree import texts as _texts


@pytest.fixture
def props(videroid_app):
    app, window = videroid_app
    app.show_page("properties")
    window.render()
    return app, window, app._pages["properties"]


def _prop(ctx, name):
    return next(p for p in ctx.get_prop_types() if p.name == name)


class TestPropActions:
    def test_actions_per_type(self, props):
        app, _, page = props
        ctx = app.context
        ctx.create_prop_type("pstr", "str", "", False)
        ctx.create_prop_type("pmul", "str", "", True)
        ctx.create_prop_type("pint", "int", 0, False)
        single = [a for a, _ in page._prop_actions(_prop(ctx, "pstr"))]
        multiple = [a for a, _ in page._prop_actions(_prop(ctx, "pmul"))]
        integer = [a for a, _ in page._prop_actions(_prop(ctx, "pint"))]
        assert "Manage values…" in single and "Move values…" not in single
        assert "Move values…" in multiple
        assert "Manage values…" not in integer  # non-str: rename + delete only


class TestRenameConvertDelete:
    def test_rename(self, props):
        app, _, page = props
        page._rename(_prop(app.context, "category"))  # opens fancybox
        page._do_rename(_prop(app.context, "category"), _T("category_x"))
        assert "category_x" in {p.name for p in app.context.get_prop_types()}

    def test_convert(self, props):
        app, _, page = props
        app.context.create_prop_type("pconv", "str", "", False)
        page._convert(_prop(app.context, "pconv"))  # confirm dialog
        page._do_convert(_prop(app.context, "pconv"))
        assert _prop(app.context, "pconv").multiple is True

    def test_delete(self, props):
        app, _, page = props
        app.context.create_prop_type("todelete", "str", "", False)
        page._delete(_prop(app.context, "todelete"))  # confirm dialog
        page._do_delete(_prop(app.context, "todelete"))
        assert "todelete" not in {p.name for p in app.context.get_prop_types()}


class TestDialogs:
    def test_manage_values(self, props):
        app, _, page = props
        page._manage_values(_prop(app.context, "category"))  # fancybox
        assert app.window.has_fancybox()

    def test_move_values_flow(self, props):
        app, _, page = props
        ctx = app.context
        db = ctx._api.database
        ctx.create_prop_type("msrc", "str", "", True)  # multiple source
        ctx.create_prop_type("mdst", "str", "", True)  # str target
        vid = ctx.get_videos(1, 0).result[0].video_id
        with db.to_save():
            db.videos_tag_set("msrc", {vid: ["move_me"]})
        source = _prop(ctx, "msrc")
        page._move_values(source)  # opens fancybox
        dialog = MoveValuesDialog(ctx, source)
        dialog._selected.add("move_me")
        dialog._target.index = next(
            i for i, t in enumerate(dialog._targets) if t.name == "mdst"
        )
        page._do_move(source, dialog)  # move_property_values + reload

        def values(name):
            return {v for vals in ctx.get_property_values(name).values() for v in vals}

        assert "move_me" not in values("msrc")  # left the source
        assert "move_me" in values("mdst")  # landed on the target

    def test_fill_flow(self, props):
        app, _, page = props
        ctx = app.context
        ctx.create_prop_type("fillme", "str", "", True)

        def values():
            return {
                v for vals in ctx.get_property_values("fillme").values() for v in vals
            }

        assert values() == set()  # empty before fill
        page._on_fill(None)  # opens fancybox
        from pysaurus.interface.videroid.dialogs.fill_property_dialog import (
            FillPropertyDialog,
        )

        dialog = FillPropertyDialog(ctx.get_prop_types())
        dialog._combo.index = next(
            i for i, p in enumerate(dialog._eligible) if p.name == "fillme"
        )
        page._do_fill(dialog)  # fill_property_with_terms + reload
        assert values()  # now filled with terms extracted from filenames


class TestCreateForm:
    def _create(self, page, name, type_index=0, default="", enum="", use_enum=False):
        page._name.value = name
        page._type.index = type_index
        page._default.value = default
        page._enum.value = enum
        page._use_enum.checked = use_enum
        page._on_create(None)

    def test_empty_name(self, props):
        _, _, page = props
        self._create(page, "")
        assert "enter a property name" in page._feedback.text

    def test_create_str(self, props):
        app, _, page = props
        self._create(page, "freshstr")
        assert "freshstr" in {p.name for p in app.context.get_prop_types()}
        assert "created" in page._feedback.text

    def test_create_int_with_default(self, props):
        app, _, page = props
        self._create(page, "freshint", type_index=1, default="5")
        assert "freshint" in {p.name for p in app.context.get_prop_types()}

    def test_create_invalid_default(self, props):
        _, _, page = props
        self._create(page, "badint", type_index=1, default="abc")
        assert "Invalid default" in page._feedback.text

    def test_create_with_enum(self, props):
        app, _, page = props
        self._create(page, "enump", use_enum=True, enum="a, b, c")
        assert "enump" in {p.name for p in app.context.get_prop_types()}

    def test_create_duplicate_reports_error(self, props):
        _, _, page = props
        self._create(page, "category")  # already exists -> backend raises
        assert "Failed to create" in page._feedback.text

    def test_reset_form(self, props):
        _, _, page = props
        page._name.value = "x"
        page._multiple.checked = True
        page._reset_form()
        assert page._name.value == "" and page._multiple.checked is False

    def test_parse_default_types(self, props):
        _, _, page = props
        assert page._parse_default("bool", "true") is True
        assert page._parse_default("int", "7") == 7
        assert page._parse_default("int", "") == 0
        assert page._parse_default("float", "1.5") == 1.5
        assert page._parse_default("str", "hello") == "hello"

    def test_reload_empty_shows_placeholder(self, props):
        app, _, page = props
        for prop in list(app.context.get_prop_types()):
            app.context.delete_prop_type(prop.name)
        page._reload()
        assert len(page._table.controls) >= 2  # header + placeholder row
        assert "(no property defined)" in _texts(page._table)


class _T:
    """Minimal stand-in for a TextInput exposing `.value`."""

    def __init__(self, value):
        self.value = value
