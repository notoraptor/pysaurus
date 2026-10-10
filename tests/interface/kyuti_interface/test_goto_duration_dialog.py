"""Tests for GoToDurationDialog."""

from PySide6.QtWidgets import QDialog

from pysaurus.interface.kyuti.dialogs.goto_duration_dialog import GoToDurationDialog


class TestGoToDurationDialog:
    def test_ok_enabled_only_for_a_valid_duration(self, qtbot):
        dialog = GoToDurationDialog(force_sorting=False)
        qtbot.addWidget(dialog)
        assert not dialog.ok_button.isEnabled()

        dialog.duration_input.setText("1h30")
        assert not dialog.ok_button.isEnabled()
        assert dialog.get_duration() is None

        dialog.duration_input.setText("1h30m")
        assert dialog.ok_button.isEnabled()
        assert dialog.get_duration().t == 5400 * 1_000_000

        dialog.duration_input.setText("1:30:15")
        assert dialog.ok_button.isEnabled()
        assert dialog.get_duration().t == 5415 * 1_000_000

    def test_warning_shown_only_when_sorting_will_be_forced(self, qtbot):
        forced = GoToDurationDialog(force_sorting=True)
        qtbot.addWidget(forced)
        assert not forced.warning_label.isHidden()

        kept = GoToDurationDialog(force_sorting=False)
        qtbot.addWidget(kept)
        assert kept.warning_label.isHidden()

    def test_get_seconds_returns_typed_duration(self, qtbot, monkeypatch):
        def fake_exec(self):
            self.duration_input.setText("2h5s")
            return QDialog.DialogCode.Accepted

        monkeypatch.setattr(GoToDurationDialog, "exec", fake_exec)
        assert GoToDurationDialog.get_seconds(force_sorting=False) == 7205.0

    def test_get_seconds_returns_none_when_cancelled(self, qtbot, monkeypatch):
        monkeypatch.setattr(
            GoToDurationDialog, "exec", lambda self: QDialog.DialogCode.Rejected
        )
        assert GoToDurationDialog.get_seconds(force_sorting=True) is None
