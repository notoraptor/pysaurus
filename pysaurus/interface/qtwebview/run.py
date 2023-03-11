import logging
import sys
import threading

import ujson as json
from PyQt5.QtCore import QMetaObject, QObject, QUrl, Q_ARG, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView
from PyQt5.QtWidgets import QApplication

from pysaurus import package_dir
from pysaurus.application import exceptions
from pysaurus.core.components import AbsolutePath
from pysaurus.core.enumeration import EnumerationError
from pysaurus.core.modules import System
from pysaurus.interface.api.gui_api import GuiAPI

logger = logging.getLogger(__name__)

LevelType = QWebEnginePage.JavaScriptConsoleMessageLevel
LOG_LEVEL = {
    LevelType.InfoMessageLevel: logger.info,
    LevelType.WarningMessageLevel: logger.warning,
    LevelType.ErrorMessageLevel: logger.error,
}


class Api(GuiAPI):
    __slots__ = ("interface",)

    def __init__(self, interface):
        super().__init__()
        self.interface = interface  # type: Interface

    def _run_thread(self, function, *args, **kwargs):
        """Override to make sure exceptions are sent to main thread.

        We send exceptions to main thread so that main thread
        can be closed if an error occurred in a derived thread.
        """

        def wrapper():
            try:
                function(*args, **kwargs)
            except Exception as exception:
                # Use Qt interface to call Qt slot `Interface.throw`
                # in main thread with raised exception as argument.
                self.threads_stop_flag = True
                QMetaObject.invokeMethod(
                    self.interface,
                    "throw",
                    Qt.QueuedConnection,
                    Q_ARG(Exception, exception),
                )

        return super()._run_thread(wrapper)

    def _notify(self, notification):
        self.interface.notified.emit(json.dumps(notification.describe()))


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
            logger.exception("API call exception")
            result = {
                "error": True,
                "data": {"name": type(exception).__name__, "message": str(exception)},
            }
        return json.dumps(result)

    @pyqtSlot(Exception)
    def throw(self, exception):
        """Special slot used to raise an exception in main thread.

        Used in Api._run_thread above. Allows to transfer an exception
        occurred from a thread to main thread so that main thread
        is notified with other thread exceptions, and then can
        decide to close program if necessary.
        """
        raise exception


class CustomPage(QWebEnginePage):
    def javaScriptConsoleMessage(
        self, level: LevelType, message: str, line_number: int, source_id: str
    ):
        log_fn = LOG_LEVEL[level]
        log_fn(f"[JS:at] {source_id}:{line_number}")
        log_fn(f"[JS] {message}")


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
        logger.debug(f"Loading {url}")
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

    def closeEvent(self, close_event) -> None:
        self.interface.api.close_app()
        return super().closeEvent(close_event)


def generate_except_hook(qapp, api: Api):
    def except_hook(cls, exception, trace):
        logger.error("[Qt] Error occurring.")
        sys.__excepthook__(cls, exception, trace)
        api.threads_stop_flag = True
        qapp.exit(1)

    return except_hook


def generate_thread_except_hook(qapp, api: Api):
    def thread_except_hook(arg):
        logger.error(f"[Qt] Error occurring in thread: {arg.thread.name}")
        sys.__excepthook__(arg.exc_type, arg.exc_value, arg.exc_traceback)
        api.threads_stop_flag = True
        qapp.exit(1)

    return thread_except_hook


def main():
    from multiprocessing import freeze_support

    # Necessary to allow to create a distribuable standalone application.
    # TODO Retrieve reference for this.
    freeze_support()

    # Initialize.
    app = QApplication.instance() or QApplication(sys.argv)
    # Set geometry.
    desktop = app.desktop()
    dpix = desktop.logicalDpiX()
    dpiy = desktop.logicalDpiY()
    screen_rect = desktop.screen().rect()
    screen_center = screen_rect.center()
    width = (7 * screen_rect.width()) // 10
    height = (2 * screen_rect.height()) // 3
    x = screen_center.x() - width // 2
    y = screen_center.y() - height // 2
    logger.debug(f"Window: pos ({x}; {y}), size {width} x {height}")
    logger.debug(f"Window: DPI {dpix} x {dpiy}")
    logger.debug(f"Window: IRL {width * 2.54 / dpix} x {height * 2.54 / dpiy} cm")
    view = PysaurusQtApplication(geometry=(x, y, width, height))
    # Set zoom.
    if System.is_windows():
        settings = view.page().settings()
        font_size = settings.fontSize(settings.FontSize.DefaultFontSize)
        font_cm = font_size * 2.54 / dpiy
        # Try to scale so that default font size is at least 0.35 cm height
        scale = 0.35 / font_cm
        logger.debug(f"Window: font {font_size} cm {font_cm} scale {scale}")
        if scale > 1:
            view.setZoomFactor(scale)
    # Set except hooks
    sys.excepthook = generate_except_hook(app, view.interface.api)
    threading.excepthook = generate_thread_except_hook(app, view.interface.api)
    # Display.
    view.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    logging.basicConfig(level=logging.NOTSET)
    main()
