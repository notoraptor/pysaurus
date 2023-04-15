from typing import Sequence, Type, Union

from PyQt6.QtWidgets import QGridLayout, QLabel, QLineEdit, QPushButton, QWidget

from pysaurus.interface.common.qt_utils import Callback, TYPE_VALIDATORS

Value = Union[str, bool, int, float]
ValueType = Type[Value]


class SetInput(QWidget):
    def __init__(self, value_type: ValueType, values: Sequence[Value] = ()):
        super().__init__()
        validator = TYPE_VALIDATORS[value_type]
        self.type = value_type
        self.values = sorted({validator(v) for v in values})
        self.__contents = []
        self.__text_input = QLineEdit()
        self.__add_button = QPushButton("+")
        self.__grid = QGridLayout()

        self.__grid.setSizeConstraint(QGridLayout.SizeConstraint.SetMinAndMaxSize)

        self.__text_input.returnPressed.connect(self.add_value)
        self.__add_button.clicked.connect(self.add_value)
        self.setLayout(self.__grid)
        self._draw()

    def add_value(self):
        text = self.__text_input.text().strip()
        if text:
            self.__text_input.setText("")
            value = TYPE_VALIDATORS[self.type].parser(text)
            values = set(self.values)
            if value not in values:
                values.add(value)
                self.values = sorted(values)
                self._draw()

    def remove_value(self, value):
        value = TYPE_VALIDATORS[self.type](value)
        values = set(self.values)
        if value in values:
            values.remove(value)
            self.values = sorted(values)
            self._draw()

    def _draw(self):
        for content in self.__contents:
            self.__grid.removeWidget(content)
        self.__contents.clear()
        i = 0
        for value in self.values:
            label = QLabel(str(value))
            button = QPushButton("-")
            button.clicked.connect(Callback(self.remove_value, value))
            self.__grid.addWidget(label, i, 0)
            self.__grid.addWidget(button, i, 1)
            self.__contents.append(label)
            self.__contents.append(button)
            i += 1
        self.__grid.addWidget(self.__text_input, i, 0)
        self.__grid.addWidget(self.__add_button, i, 1)
