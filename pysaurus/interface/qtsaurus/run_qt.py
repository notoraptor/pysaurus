import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QScrollArea, QVBoxLayout, QWidget

from pysaurus.interface.api.gui_api import GuiAPI
from pysaurus.interface.common.qt_utils import ExceptHookForQt
from pysaurus.interface.qtsaurus.set_input import SetInput


class MyAPI(GuiAPI):
    __slots__ = ()


class MyExceptHook(ExceptHookForQt):
    __slots__ = ()

    def cleanup(self):
        print("Except hook cleanup.")


class QtSaurus(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pysaurus")
        si = SetInput(int, [1, 2, 4, 5])
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(si)
        layout.addStretch()
        widget.setLayout(layout)
        sa = QScrollArea()
        sa.setWidget(widget)
        self.setCentralWidget(sa)


def main():
    app = QApplication(sys.argv)
    MyExceptHook(app).register()
    window = QtSaurus()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
