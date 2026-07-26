"""Radio-button editor for a bool property."""

from PySide6.QtCore import QEvent, Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QRadioButton, QWidget

from pysaurus.core.language import say


class BoolValueWidget(QWidget):
    """Radio buttons for a bool property, optionally with a "not set" state.

    A checkbox cannot tell why it is unticked: because the value is False, or
    because the video carries no value for that property at all. Radio buttons
    make the difference visible.

    "Not set" is *not* a third value -- the domain of a bool stays exactly
    {False, True} (see properties.OPEN_DOMAIN_PROP_TYPES). It stands for the
    absence of a stored value, which the database already models as the absence
    of a row, so picking it means clearing the property rather than writing to
    it. Callers that have their own way of expressing "leave it alone" (batch
    edit, where a separate checkbox arms the change) pass with_undefined=False.
    """

    changed = Signal()

    def __init__(self, with_undefined: bool = True, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        states: list[bool | None] = [False, True]
        if with_undefined:
            states.insert(0, None)

        self._group = QButtonGroup(self)
        self._buttons: list[tuple[bool | None, QRadioButton]] = []
        for state in states:
            button = QRadioButton(self._label(state))
            self._group.addButton(button)
            self._buttons.append((state, button))
            layout.addWidget(button)
        layout.addStretch()

        # buttonClicked only fires on user interaction, so set_value() stays
        # silent and callers need no loading guard around it.
        self._group.buttonClicked.connect(self._on_button_clicked)
        self.setFocusProxy(self._buttons[0][1])
        self.set_value(states[0])

    @staticmethod
    def _label(state: bool | None) -> str:
        if state is None:
            return say("Not set")
        return say("Yes") if state else say("No")

    def _on_button_clicked(self, _button) -> None:
        self.changed.emit()

    def value(self) -> bool | None:
        """Return the selected state, None meaning "no value"."""
        for state, button in self._buttons:
            if button.isChecked():
                return state
        return None

    def set_value(self, value: bool | None) -> None:
        """Select the state matching `value`, without emitting `changed`.

        Checking the target is enough to clear the others (the group is
        exclusive). A value this widget cannot show -- None when it has no
        "not set" button -- falls back to the first state.
        """
        target = None if value is None else bool(value)
        for state, button in self._buttons:
            if state is target:
                button.setChecked(True)
                return
        self._buttons[0][1].setChecked(True)

    def retranslateUi(self) -> None:
        """Re-apply the button labels in the current language."""
        for state, button in self._buttons:
            button.setText(self._label(state))

    def changeEvent(self, event):
        """Qt posts LanguageChange to every widget when a QTranslator is
        installed or removed. Handled here rather than by the owning dialog,
        so this widget stays self-contained wherever it is used."""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)
