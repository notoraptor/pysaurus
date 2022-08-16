import os
import sys
import tempfile
import threading
import traceback
from multiprocessing import freeze_support

import ujson as json
from PyQt5.QtCore import QObject, QUrl, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView
from PyQt5.QtWidgets import QApplication

from other.bad_saurus.gui import theria
from pysaurus.core.modules import System

freeze_support()


def html_to_file_path(html: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as tf:
        tf.write(html)
        return tf.name


def generate_except_hook(qapp, original_excepthook):
    def except_hook(cls, exception, traceback):
        print("[Qt] uncaught error", file=sys.stderr)
        original_excepthook(cls, exception, traceback)
        qapp.exit(1)

    return except_hook


def generate_thread_except_hook(qapp, original_excepthook):
    def thread_except_hook(arg):
        print("[Qt] error occurring in thread:", arg.thread.name, file=sys.stderr)
        original_excepthook(arg.exc_type, arg.exc_value, arg.exc_traceback)
        qapp.exit(1)

    return thread_except_hook


class Interface(QObject):
    def __init__(self, renderer, parent=None):
        super().__init__(parent)
        self.renderer = renderer

    # Signal to notify about data updates
    updated = pyqtSignal()
    # Signal to notify about a fancybox HTML content to display
    dialog = pyqtSignal(str)

    def run(self, name: str, args):
        instance, method_name = self.renderer.calls[name]
        print("[call]", name, args)
        view = self.renderer.render_call(instance, method_name)
        if view:
            # View needed for this call. Display a fancy box.
            if args:
                # No view needed for this call. Execute it immediately
                (kwargs,) = args
                result = getattr(instance, method_name)(**kwargs)
                # Assume data updates and signal it
                self.updated.emit()
                return result
            else:
                self.dialog.emit(view)
        else:
            # No view needed for this call. Execute it immediately
            result = getattr(instance, method_name)(*args)
            # Assume data updates and signal it
            self.updated.emit()
            return result

    @pyqtSlot(str, result=str)
    def call(self, json_str):
        try:
            result = {"error": False, "data": self.run(*json.loads(json_str))}
        except Exception as exception:
            traceback.print_tb(exception.__traceback__, file=sys.stderr)
            print(type(exception), exception, file=sys.stderr)
            result = {
                "error": True,
                "data": {"name": type(exception).__name__, "message": str(exception)},
            }
        return json.dumps(result)


class CustomPage(QWebEnginePage):
    LevelType = QWebEnginePage.JavaScriptConsoleMessageLevel
    LEVEL = {
        LevelType.InfoMessageLevel: "info",
        LevelType.WarningMessageLevel: "warning",
        LevelType.ErrorMessageLevel: "error",
    }

    def javaScriptConsoleMessage(
        self, level: LevelType, message: str, line_number: int, source_id: str
    ):
        file = sys.stdout if level == self.LevelType.InfoMessageLevel else sys.stderr
        print(f"[Qt/JS:{self.LEVEL[level]}] {source_id}:{line_number}", file=file)
        print(f"\t{message}", file=file)


class View(QWebEngineView):
    QT_SCRIPT_URL = QUrl.fromLocalFile(os.path.join(os.path.dirname(__file__), "qt.js"))

    def __init__(self, data):
        super().__init__()
        self.renderer = theria.Renderer(
            data,
            header_scripts=["qrc:///qtwebchannel/qwebchannel.js"],
            body_scripts=[self.QT_SCRIPT_URL.toString()],
        )

        # setup page
        self.web_page = CustomPage()
        self.web_page.setUrl(QUrl.fromLocalFile(html_to_file_path(self.renderer.html)))
        self.setPage(self.web_page)

        # setup channel
        self.interface = Interface(self.renderer)
        self.channel = QWebChannel()
        self.channel.registerObject("backend", self.interface)
        self.page().setWebChannel(self.channel)
        self.interface.updated.connect(self.reload_page)
        self.interface.dialog.connect(self.load_fancy_box)

        # setup fancy box
        self.fancy_box = None

    def set_view(self, app: QApplication):
        # Set geometry.
        screen_rect = app.desktop().screen().rect()
        screen_center = screen_rect.center()
        width = (7 * screen_rect.width()) // 10
        height = (2 * screen_rect.height()) // 3
        x = screen_center.x() - width // 2
        y = screen_center.y() - height // 2
        print(
            f"[Qt/window] size {width} x {height}, position ({x}; {y})", file=sys.stderr
        )
        self.setGeometry(x, y, width, height)
        # Set zoom.
        if System.is_windows():
            # view.setZoomFactor(1.8)
            screen_height = screen_rect.height()
            base_height = 1080
            if screen_height > base_height:
                scale = (screen_height / base_height) * 0.9
                print("[Qt/window] scale", scale)
                self.setZoomFactor(scale)

    def reload_page(self):
        self.web_page.setUrl(QUrl.fromLocalFile(html_to_file_path(self.renderer.html)))

    def load_fancy_box(self, html):
        print("[fancybox]")
        print(html)
        if self.fancy_box:
            del self.fancy_box
        self.fancy_box = FancyBox(self.interface, title="Form", html=html)
        self.fancy_box.show()


class FancyBox(QWebEngineView):
    def __init__(self, interface, title="", html=""):
        super().__init__()
        self.setWindowTitle(title)
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(800, 600)

        # setup page
        self.web_page = CustomPage()
        self.web_page.setUrl(
            QUrl.fromLocalFile(html_to_file_path(html or f"<h1>{title}</h1>"))
        )
        # self.web_page.setHtml(html or f"<h1>{title}</h1>")
        self.setPage(self.web_page)

        # setup channel
        self.channel = QWebChannel()
        self.channel.registerObject("backend", interface)
        self.page().setWebChannel(self.channel)

        self.set_view(QApplication.instance())

    def set_view(self, app: QApplication):
        # Set geometry.
        screen_rect = app.desktop().screen().rect()
        # Set zoom.
        if System.is_windows():
            # view.setZoomFactor(1.8)
            screen_height = screen_rect.height()
            base_height = 1080
            if screen_height > base_height:
                scale = (screen_height / base_height) * 0.9
                print("[Qt/window] scale", scale)
                self.setZoomFactor(scale)


def gui(data):
    # Initialize.
    app = QApplication.instance() or QApplication(sys.argv)
    # original_excepthook = sys.__excepthook__
    original_excepthook = sys.excepthook
    sys.excepthook = generate_except_hook(app, original_excepthook)
    threading.excepthook = generate_thread_except_hook(app, original_excepthook)
    view = View(data)
    view.set_view(app)
    # Display.
    view.show()
    return app.exec_()
