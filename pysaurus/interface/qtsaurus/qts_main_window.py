from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QMainWindow

from pysaurus.core.notifications import Notification
from pysaurus.core.notifying import Notifier
from pysaurus.interface.api.gui_api import GuiAPI


class Interface(QtCore.QObject):
    notified = QtCore.Signal(Notification)


class QtsAPI(GuiAPI):
    """Qts = Qt Saurus"""

    __slots__ = ("interface",)

    def __init__(self, interface: Interface):
        super().__init__()
        self.interface = interface

    def _notify(self, notification):
        self.interface.notified.emit(notification)


class _LocalNotifier(Notifier):
    __slots__ = ()

    def __init__(self):
        super().__init__()
        self.never_call_default_manager()


class QtsMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.interface = Interface()
        self.api = QtsAPI(self.interface)
        self.gui_notifier = _LocalNotifier()
        self.interface.notified.connect(self.notify)

    def call(self, name: str, *args):
        return self.api.__run_feature__(name, *args)

    def notify(self, notification):
        self.gui_notifier.notify(notification)

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        print("Show event.")
        return super().showEvent(a0)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.api.close_app()
        return super().closeEvent(event)
