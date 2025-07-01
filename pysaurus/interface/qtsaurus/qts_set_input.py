from typing import Sequence, Type

from PySide6.QtWidgets import QGridLayout, QLineEdit, QPushButton, QWidget

from pysaurus.interface.common.qt_utils import Callback, TYPE_VALIDATORS
from pysaurus.interface.qtsaurus.qts_alerter import QtsAlerter
from pysaurus.interface.qtsaurus.qts_elided_label import QtsElidedLabel

Value = str | bool | int | float
ValueType = Type[Value]


class QtsSetInput(QWidget):
    def __init__(self, value_type: ValueType, values: Sequence[Value] = ()):
        super().__init__()
        validator = TYPE_VALIDATORS[value_type]
        self.__type = value_type
        self.__values = sorted({validator(v) for v in values})
        self.__contents = []

        self.__text_input = QLineEdit()
        self.__add_button = QPushButton("+")
        self.__grid = QGridLayout()

        self.__text_input.returnPressed.connect(self._add_value)
        self.__add_button.clicked.connect(self._add_value)

        self.__grid.setSizeConstraint(QGridLayout.SizeConstraint.SetMinAndMaxSize)
        self.setLayout(self.__grid)
        self._draw()

    def values(self) -> Sequence[Value]:
        return self.__values

    def _add_value(self):
        text = self.__text_input.text().strip()
        if text:
            with QtsAlerter(self, "Parsing error"):
                self.__text_input.setText("")
                value = TYPE_VALIDATORS[self.__type].parse(text)
                values = set(self.__values)
                if value not in values:
                    values.add(value)
                    self.__values = sorted(values)
                    self._draw()

    def _remove_value(self, value):
        value = TYPE_VALIDATORS[self.__type](value)
        values = set(self.__values)
        if value in values:
            values.remove(value)
            self.__values = sorted(values)
            self._draw()

    def _draw(self):
        for content in self.__contents:
            self.__grid.removeWidget(content)
        self.__contents.clear()
        for i, value in enumerate(self.__values):
            label = QtsElidedLabel(str(value))
            button = QPushButton("-")
            button.clicked.connect(Callback(self._remove_value, value))
            self.__grid.addWidget(label, i, 0)
            self.__grid.addWidget(button, i, 1)
            self.__contents.append(label)
            self.__contents.append(button)
        self.__grid.addWidget(self.__text_input, len(self.__values), 0)
        self.__grid.addWidget(self.__add_button, len(self.__values), 1)
        self.__contents.append(self.__text_input)
        self.__contents.append(self.__add_button)
