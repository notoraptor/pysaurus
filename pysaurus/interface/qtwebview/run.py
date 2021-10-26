import sys
import threading
import traceback

import ujson as json
from PyQt5.QtCore import QMetaObject, QObject, QUrl, Q_ARG, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView
from PyQt5.QtWidgets import QApplication

from pysaurus.application import exceptions
from pysaurus.core.components import AbsolutePath
from pysaurus.core.functions import package_dir
from pysaurus.core.modules import System
from pysaurus.core.notifications import Notification
from pysaurus.interface.api.gui_api import GuiAPI

try:
    from pysaurus.interface.qtwebview.player import Player

    has_vlc = True
except RuntimeError as exc:
    print("Unable to import VLC player", file=sys.stderr)
    print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
    has_vlc = False

LevelType = QWebEnginePage.JavaScriptConsoleMessageLevel
LEVEL = {
    LevelType.InfoMessageLevel: "info",
    LevelType.WarningMessageLevel: "warning",
    LevelType.ErrorMessageLevel: "error",
}


class NextRandomVideo(Notification):
    __slots__ = ()


class Api(GuiAPI):
    PYTHON_HAS_EMBEDDED_PLAYER = has_vlc

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

    def open_random_player(self):
        self.interface.player_triggered.emit()


class Interface(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = Api(self)

    # Slot set in Javascript code
    notified = pyqtSignal(str)
    # Slot set in Python code below
    player_triggered = pyqtSignal()

    @pyqtSlot(str, result=str)
    def call(self, json_str):
        try:
            func_name, func_args = json.loads(json_str)
            assert not func_name.startswith("_")
            result = {"error": False, "data": getattr(self.api, func_name)(*func_args)}
        except (OSError, exceptions.PysaurusError) as exception:
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
    def __init__(self, *, geometry=None):
        super().__init__()

        # setup interface
        self.interface = Interface()

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

        # setup player
        self.player = None
        if has_vlc:
            self.player = Player(on_next=self._on_next_random_video)
            self.interface.player_triggered.connect(self.player.show)
            if geometry:
                _, _, width, height = geometry
                self.player.resize(int(width * 3 / 4), int(height * 3 / 4))

    def _on_next_random_video(self):
        video = self.interface.api.choose_random_video()
        self.interface.api._notify(NextRandomVideo())
        return video.filename.path


def generate_except_hook(qapp):
    def except_hook(cls, exception, traceback):
        sys.__excepthook__(cls, exception, traceback)
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
