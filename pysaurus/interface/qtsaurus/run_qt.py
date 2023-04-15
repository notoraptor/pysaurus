import logging
import sys

from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from pysaurus.core.notifications import Notification
from pysaurus.interface.api.gui_api import GuiAPI
from pysaurus.interface.common.qt_saurus_utils import PysaurusQtExceptHook
from pysaurus.interface.qtsaurus.set_input import SetInput


class Interface(QtCore.QObject):
    notified = QtCore.pyqtSignal(Notification)


class MyAPI(GuiAPI):
    __slots__ = ("interface",)

    def __init__(self, interface: Interface):
        super().__init__()
        self.interface = interface

    def _notify(self, notification):
        self.interface.notified.emit(notification)


class QtSaurus(QMainWindow):
    def __init__(self):
        super().__init__()
        self.interface = Interface()
        self.api = MyAPI(self.interface)
        self.interface.notified.connect(self.inform)

        self.setWindowTitle("Pysaurus")
        si = SetInput(int, [1, 2, 4, 5])
        bt = QPushButton("notify")
        bt.clicked.connect(self.send)
        vbl = QVBoxLayout()
        wdg = QWidget()
        vbl.setContentsMargins(0, 0, 0, 0)
        vbl.addWidget(si)
        vbl.addWidget(bt)
        wdg.setLayout(vbl)

        sa = QScrollArea()
        sa.setWidgetResizable(True)
        # sa.setWidget(si)
        self.setCentralWidget(wdg)

    def send(self):
        print(self.api.__run_feature__("get_constants"))
        self.api.notifier.notify(Notification())

    def inform(self, notification):
        print("Informed", notification)

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        print("Show event.")
        return super().showEvent(a0)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.api.close_app()
        return super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = QtSaurus()
    PysaurusQtExceptHook(app, window.api).register()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    main()
