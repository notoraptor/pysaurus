"""The advanced tab of SourcesDialog lists, loads, saves, renames and deletes.

Three states derive from the editor text: empty, unsaved, saved. The combo,
the buttons and the error follow the text; a combo choice only rewrites it.
Save shows in the first two states, Rename in the third.
"""

import pytest
from PySide6.QtCore import Qt

from pysaurus.application.exceptions import PysaurusError
from pysaurus.database.saved_search import SavedSearch
from pysaurus.interface.kyuti.dialogs import sources_dialog
from pysaurus.interface.kyuti.dialogs.sources_dialog import SourcesDialog
from pysaurus.interface.kyuti.utils.text import LABEL_MAX_LENGTH

NONE_ENTRY = "(select a saved search)"


@pytest.fixture
def ctx(mock_context):
    mock_context.save_search("width > 100", "wide")
    mock_context.save_search("height > 100")
    return mock_context


def _combo_labels(dialog: SourcesDialog) -> list[str]:
    combo = dialog._saved_combo
    return [combo.itemText(i) for i in range(1, combo.count())]


def _buttons(dialog: SourcesDialog) -> tuple[str, bool, bool]:
    """(which of save/rename shows, it is enabled, delete is enabled)."""
    save_shown = not dialog._save_button.isHidden()
    rename_shown = not dialog._rename_button.isHidden()
    assert save_shown != rename_shown
    shown = dialog._save_button if save_shown else dialog._rename_button
    return (
        "save" if save_shown else "rename",
        shown.isEnabled(),
        dialog._delete_button.isEnabled(),
    )


def _answer_name(monkeypatch, name: str | None):
    """Make the name prompt answer `name`, or cancel when None."""
    monkeypatch.setattr(
        sources_dialog.QInputDialog,
        "getText",
        lambda *a, **k: (name or "", name is not None),
    )


def test_without_context_the_bar_is_hidden(qtbot):
    dialog = SourcesDialog()
    qtbot.addWidget(dialog)
    assert dialog._saved_bar.isHidden()


def test_combo_lists_saved_searches_by_label(qtbot, ctx):
    dialog = SourcesDialog(ctx=ctx)
    qtbot.addWidget(dialog)
    assert not dialog._saved_bar.isHidden()
    assert dialog._saved_combo.itemText(0) == NONE_ENTRY
    assert dialog._saved_combo.itemData(0, Qt.ItemDataRole.ToolTipRole) == NONE_ENTRY
    assert _combo_labels(dialog) == ["wide", "height > 100"]


def test_long_labels_are_elided_but_data_is_whole(qtbot, ctx):
    long_expression = "width > " + "1" * 100
    ctx.save_search(long_expression)
    dialog = SourcesDialog(ctx=ctx)
    qtbot.addWidget(dialog)
    label = _combo_labels(dialog)[-1]
    assert len(label) == LABEL_MAX_LENGTH
    assert label.endswith("...")
    assert dialog._saved_combo.itemData(3) == long_expression


def test_combo_tooltip_shows_the_whole_current_entry(qtbot, ctx):
    long_expression = "width > " + "1" * 100
    ctx.save_search(long_expression)
    dialog = SourcesDialog(ctx=ctx)
    qtbot.addWidget(dialog)
    assert dialog._saved_combo.toolTip() == NONE_ENTRY
    dialog._expression_edit.setPlainText(long_expression)
    assert dialog._saved_combo.toolTip() == long_expression
    dialog._expression_edit.setPlainText("width > 100")
    assert dialog._saved_combo.toolTip() == "wide: width > 100"
    assert dialog._saved_combo.itemData(1, Qt.ItemDataRole.ToolTipRole) == (
        "wide: width > 100"
    )


# Editor text -> combo and buttons


def test_empty_text_selects_none_and_disables_everything(qtbot, ctx):
    dialog = SourcesDialog(ctx=ctx)
    qtbot.addWidget(dialog)
    assert dialog._saved_combo.currentIndex() == 0
    assert _buttons(dialog) == ("save", False, False)


def test_unsaved_text_selects_none_and_allows_save_only(qtbot, ctx):
    dialog = SourcesDialog(current_expression="width > 101", ctx=ctx)
    qtbot.addWidget(dialog)
    assert dialog._saved_combo.currentIndex() == 0
    assert _buttons(dialog) == ("save", True, False)


def test_saved_text_selects_its_entry_and_allows_rename_and_delete(qtbot, ctx):
    dialog = SourcesDialog(current_expression="height > 100", ctx=ctx)
    qtbot.addWidget(dialog)
    assert dialog._saved_combo.currentData() == "height > 100"
    assert _buttons(dialog) == ("rename", True, True)


def test_editing_the_text_moves_between_states(qtbot, ctx):
    dialog = SourcesDialog(current_expression="width > 100", ctx=ctx)
    qtbot.addWidget(dialog)
    dialog._expression_edit.setPlainText("width > 101")
    assert dialog._saved_combo.currentIndex() == 0
    assert _buttons(dialog) == ("save", True, False)
    dialog._expression_edit.setPlainText("  width > 100  ")
    assert dialog._saved_combo.currentIndex() == 1
    assert _buttons(dialog) == ("rename", True, True)
    dialog._expression_edit.setPlainText("   ")
    assert dialog._saved_combo.currentIndex() == 0
    assert _buttons(dialog) == ("save", False, False)


# Combo choice -> editor text


def test_choosing_an_entry_loads_its_expression(qtbot, ctx):
    dialog = SourcesDialog(ctx=ctx)
    qtbot.addWidget(dialog)
    dialog._on_saved_search_activated(1)
    assert dialog.get_expression() == "width > 100"
    assert dialog._saved_combo.currentIndex() == 1
    assert _buttons(dialog) == ("rename", True, True)


def test_choosing_the_none_entry_clears_a_loaded_search(qtbot, ctx):
    dialog = SourcesDialog(current_expression="width > 100", ctx=ctx)
    qtbot.addWidget(dialog)
    dialog._on_saved_search_activated(0)
    assert dialog.get_expression() is None
    assert dialog._saved_combo.currentIndex() == 0
    assert _buttons(dialog) == ("save", False, False)


def test_rechoosing_the_none_entry_keeps_unsaved_text(qtbot, ctx):
    dialog = SourcesDialog(current_expression="width > 101", ctx=ctx)
    qtbot.addWidget(dialog)
    dialog._on_saved_search_activated(0)
    assert dialog.get_expression() == "width > 101"


# Save, rename, delete


def test_save_prompts_for_a_name_and_persists(qtbot, ctx, monkeypatch):
    _answer_name(monkeypatch, "fast")
    dialog = SourcesDialog(current_expression="fps > 30", ctx=ctx)
    qtbot.addWidget(dialog)
    dialog._on_save_search()
    assert SavedSearch("fps > 30", "fast") in ctx.get_saved_searches()
    assert dialog._saved_combo.currentData() == "fps > 30"
    assert _buttons(dialog) == ("rename", True, True)


def test_cancelled_save_changes_nothing(qtbot, ctx, monkeypatch):
    _answer_name(monkeypatch, None)
    dialog = SourcesDialog(current_expression="fps > 30", ctx=ctx)
    qtbot.addWidget(dialog)
    dialog._on_save_search()
    assert len(ctx.get_saved_searches()) == 2
    assert _buttons(dialog) == ("save", True, False)


def test_rename_prefills_the_current_name_and_persists(qtbot, ctx, monkeypatch):
    captured = {}

    def fake_get_text(*args, **kwargs):
        captured.update(kwargs)
        return "large", True

    monkeypatch.setattr(sources_dialog.QInputDialog, "getText", fake_get_text)
    dialog = SourcesDialog(current_expression="width > 100", ctx=ctx)
    qtbot.addWidget(dialog)
    dialog._on_rename_search()
    assert captured["text"] == "wide"
    assert SavedSearch("width > 100", "large") in ctx.get_saved_searches()
    assert "wide" not in [s.name for s in ctx.get_saved_searches()]
    assert dialog._saved_combo.currentText() == "large"
    assert dialog.get_expression() == "width > 100"


def test_rename_prefills_nothing_for_an_unnamed_search(qtbot, ctx, monkeypatch):
    captured = {}

    def fake_get_text(*args, **kwargs):
        captured.update(kwargs)
        return "", False

    monkeypatch.setattr(sources_dialog.QInputDialog, "getText", fake_get_text)
    dialog = SourcesDialog(current_expression="height > 100", ctx=ctx)
    qtbot.addWidget(dialog)
    dialog._on_rename_search()
    assert captured["text"] == ""


def test_save_error_is_shown_inline(qtbot, ctx, monkeypatch):
    _answer_name(monkeypatch, "x")

    def refuse(expression, name=None):
        raise PysaurusError("bad")

    monkeypatch.setattr(ctx, "save_search", refuse)
    dialog = SourcesDialog(current_expression="width >", ctx=ctx)
    qtbot.addWidget(dialog)
    dialog._on_save_search()
    assert not dialog._expression_error.isHidden()
    assert dialog._expression_error.text() == "bad"


def test_error_follows_the_expression_that_caused_it(qtbot, ctx, monkeypatch):
    _answer_name(monkeypatch, "x")

    def refuse(expression, name=None):
        raise PysaurusError("bad")

    monkeypatch.setattr(ctx, "save_search", refuse)
    dialog = SourcesDialog(current_expression="width >", ctx=ctx)
    qtbot.addWidget(dialog)
    dialog._on_save_search()
    dialog._expression_edit.setPlainText("  width >  ")
    assert not dialog._expression_error.isHidden()
    dialog._expression_edit.setPlainText("width > 1")
    assert dialog._expression_error.isHidden()
    dialog._expression_edit.setPlainText("width >")
    assert dialog._expression_error.isHidden()


def test_delete_removes_the_entry_and_keeps_the_text(qtbot, ctx):
    dialog = SourcesDialog(current_expression="width > 100", ctx=ctx)
    qtbot.addWidget(dialog)
    dialog._on_delete_search()
    assert [s.expression for s in ctx.get_saved_searches()] == ["height > 100"]
    assert dialog.get_expression() == "width > 100"
    assert dialog._saved_combo.currentIndex() == 0
    assert _buttons(dialog) == ("save", True, False)
