import sys

import ujson as json
from PyQt5.QtCore import pyqtSlot, QUrl, pyqtSignal, QObject
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWidgets import QApplication

from pysaurus.core.components import AbsolutePath
from pysaurus.core.functions import package_dir
from pysaurus.core.modules import System
from pysaurus.interface.cefgui.gui_api import GuiAPI

LevelType = QWebEnginePage.JavaScriptConsoleMessageLevel
LEVEL = {
    LevelType.InfoMessageLevel: "info",
    LevelType.WarningMessageLevel: "warning",
    LevelType.ErrorMessageLevel: "error",
}


class Api(GuiAPI):
    def __init__(self, interface):
        super().__init__()
        self.interface = interface  # type: Interface

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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = Api(self)

    notified = pyqtSignal(str)

    @pyqtSlot(str, result=str)
    def call(self, json_str):
        try:
            func_name, func_args = json.loads(json_str)
            assert not func_name.startswith("_")
            result = {"error": False, "data": getattr(self.api, func_name)(*func_args)}
        except Exception as exc:
            result = {
                "error": True,
                "data": {"name": type(exc).__name__, "message": str(exc)},
            }
        return json.dumps(result)


class CustomPage(QWebEnginePage):
    def javaScriptConsoleMessage(
        self, level: LevelType, message: str, line_number: int, source_id: str
    ):
        file = sys.stdout if level == LevelType.InfoMessageLevel else sys.stderr
        print(f"[JS:{LEVEL[level]}] {source_id}:{line_number}", file=file)
        print(f"\t{message}", file=file)


class HelloWorldHtmlApp(QWebEngineView):
    def __init__(self):
        super().__init__()
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
            """<script src="qrc:///qtwebchannel/qwebchannel.js"></script>""",
        )
        html = html.replace("<!--bodyScript-->", """<script src="qt.js"></script>""")
        self.web_page = CustomPage()
        self.web_page.setHtml(html, url)
        self.setPage(self.web_page)

        if System.is_windows():
            self.setZoomFactor(1.5)

        # setup channel
        self.channel = QWebChannel()
        self.channel.registerObject("backend", self.interface)
        self.page().setWebChannel(self.channel)


def main():
    # Initialize.
    app = QApplication.instance() or QApplication(sys.argv)
    view = HelloWorldHtmlApp()
    screen_rect = app.desktop().screen().rect()
    screen_center = screen_rect.center()
    # Set geometry.
    width = (2 * screen_rect.width()) // 3
    height = screen_rect.height() // 2
    x = screen_center.x() - width // 2
    y = screen_center.y() - height // 2
    print(f"Window: size {width} x {height}, position ({x}; {y})")
    view.setGeometry(x, y, width, height)
    # Display.
    view.show()
    exit(app.exec_())


if __name__ == "__main__":
    main()
