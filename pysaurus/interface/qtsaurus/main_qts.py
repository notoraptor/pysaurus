import logging
import sys

from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from pysaurus.core.notifications import Notification
from pysaurus.interface.common.qt_saurus_utils import PysaurusQtExceptHook
from pysaurus.interface.qtsaurus.qts_main_window import QtsMainWindow
from pysaurus.interface.qtsaurus.qts_path_input import QtsPathInput
from pysaurus.interface.qtsaurus.qts_set_input import QtsSetInput


class QtSaurus(QtsMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pysaurus")
        si = QtsSetInput(int, [1, 2, 4, 5])
        pi = QtsPathInput(["a", "b", "c"])
        bt = QPushButton("notify")
        bt.clicked.connect(self.send)
        vbl = QVBoxLayout()
        wdg = QWidget()
        vbl.setContentsMargins(0, 0, 0, 0)
        vbl.addWidget(si)
        vbl.addWidget(pi)
        vbl.addWidget(bt)
        wdg.setLayout(vbl)

        sa = QScrollArea()
        sa.setWidgetResizable(True)
        # sa.setWidget(si)
        self.setCentralWidget(wdg)

    def send(self):
        print(self.call("get_constants"))
        self.api.notifier.notify(Notification())


class QtSaurus2(QtsMainWindow):
    def __init__(self):
        super().__init__()
        si = QtsSetInput(float, [False, True, -2, 7.7, 1e12])
        self.setCentralWidget(si)


def main():
    app = QApplication(sys.argv)
    window = QtSaurus2()
    PysaurusQtExceptHook(app, window.api).register()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    main()
