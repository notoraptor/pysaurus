import sys
import threading
import traceback

import ujson as json
from PyQt5.QtCore import QMetaObject, QObject, QUrl, Q_ARG, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView
from PyQt5.QtWidgets import QApplication

from pysaurus.application import exceptions
from pysaurus.application.utils import package_dir
from pysaurus.core.components import AbsolutePath
from pysaurus.core.enumeration import EnumerationError
from pysaurus.core.modules import System
from pysaurus.interface.api.gui_api import GuiAPI

LevelType = QWebEnginePage.JavaScriptConsoleMessageLevel
LEVEL = {
    LevelType.InfoMessageLevel: "info",
    LevelType.WarningMessageLevel: "warning",
    LevelType.ErrorMessageLevel: "error",
}


class Api(GuiAPI):
    __slots__ = ("interface",)

    def __init__(self, interface):
        super().__init__()
        self.interface = interface  # type: Interface

    def _run_thread(self, function, *args, **kwargs):
        def wrapper():
            try:
                function(*args, **kwargs)
            except Exception as exception:
                self.threads_stop_flag = True
                QMetaObject.invokeMethod(
                    self.interface,
                    "throw",
                    Qt.QueuedConnection,
                    Q_ARG(Exception, exception),
                )

        return super()._run_thread(wrapper)

    def _notify(self, notification):
        self.interface.notified.emit(
            json.dumps(
                {
                    "name": type(notification).__name__,
                    "notification": notification.to_dict(),
                    "message": str(notification),
                }
            )
        )


class Interface(QObject):
    __api_cls__ = Api

    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = self.__api_cls__(self)

    # Slot set in Javascript code
    notified = pyqtSignal(str)

    @pyqtSlot(str, result=str)
    def call(self, json_str):
        try:
            name, args = json.loads(json_str)
            result = {"error": False, "data": self.api.__run_feature__(name, *args)}
        except (OSError, EnumerationError, exceptions.PysaurusError) as exception:
            traceback.print_tb(exception.__traceback__, file=sys.stderr)
            print(type(exception), exception, file=sys.stderr)
            result = {
                "error": True,
                "data": {"name": type(exception).__name__, "message": str(exception)},
            }
        return json.dumps(result)

    @pyqtSlot(Exception)
    def throw(self, exception):
        raise exception


class CustomPage(QWebEnginePage):
    def javaScriptConsoleMessage(
        self, level: LevelType, message: str, line_number: int, source_id: str
    ):
        file = sys.stdout if level == LevelType.InfoMessageLevel else sys.stderr
        print(f"[JS:{LEVEL[level]}] {source_id}:{line_number}", file=file)
        print(f"\t{message}", file=file)


class PysaurusQtApplication(QWebEngineView):
    __interface_cls__ = Interface

    def __init__(self, *, geometry=None):
        super().__init__()

        # setup interface
        self.interface = self.__interface_cls__()

        # setup page
        html_path = AbsolutePath.join(
            package_dir(), "interface", "web", "index.html"
        ).assert_file()
        url = QUrl.fromLocalFile(html_path.path)
        print("Loading", url)
        with open(html_path.path) as file:
            html = file.read()
        html = html.replace(
            "<!--headerScript-->",
            '<script src="qrc:///qtwebchannel/qwebchannel.js"></script>',
        )
        html = html.replace(
            '<script src="onload.js"></script>', '<script src="qt.js"></script>'
        )
        self.web_page = CustomPage()
        self.web_page.setHtml(html, url)
        self.setPage(self.web_page)

        # setup channel
        self.channel = QWebChannel()
        self.channel.registerObject("backend", self.interface)
        self.page().setWebChannel(self.channel)

        # setup geometry
        if geometry:
            assert isinstance(geometry, (tuple, list))
            assert len(geometry) == 4
            self.setGeometry(*geometry)


def generate_except_hook(qapp):
    def except_hook(cls, exception, trace):
        sys.__excepthook__(cls, exception, trace)
        qapp.exit(1)

    return except_hook


def generate_thread_except_hook(qapp):
    def thread_except_hook(arg):
        print("[Qt] Error occurring in thread:", arg.thread.name, file=sys.stderr)
        sys.__excepthook__(arg.exc_type, arg.exc_value, arg.exc_traceback)
        qapp.exit(1)

    return thread_except_hook


def main():
    from multiprocessing import freeze_support

    freeze_support()
    # Initialize.
    app = QApplication.instance() or QApplication(sys.argv)
    sys.excepthook = generate_except_hook(app)
    threading.excepthook = generate_thread_except_hook(app)
    # Set geometry.
    screen_rect = app.desktop().screen().rect()
    screen_center = screen_rect.center()
    width = (7 * screen_rect.width()) // 10
    height = (2 * screen_rect.height()) // 3
    x = screen_center.x() - width // 2
    y = screen_center.y() - height // 2
    print(f"Window: size {width} x {height}, position ({x}; {y})", file=sys.stderr)
    view = PysaurusQtApplication(geometry=(x, y, width, height))
    # Set zoom.
    if System.is_windows():
        # view.setZoomFactor(1.8)
        screen_height = screen_rect.height()
        base_height = 1080
        if screen_height > base_height:
            scale = (screen_height / base_height) * 0.9
            print("Scale", scale)
            view.setZoomFactor(scale)
    # Display.
    view.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
